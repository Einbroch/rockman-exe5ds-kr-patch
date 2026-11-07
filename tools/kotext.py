#!/usr/bin/env python3
"""번역 메모리·문자 배정·TPL 치환·재인코딩.

인코딩 설계(docs/analysis.md 「인코딩」):
- 유지: 00 빈칸, 01~0A 숫자, 67~99 라틴·기호, E4 xx 라틴 소문자 등(idx = 0xE4+xx, 폰트 제자리).
- 한글 1바이트: 0x0B~0x66, 0x9A~0xDD. 자주 쓰는 음절. 폰트 칸에 제자리로 그린다(idx = 코드).
- 한글 2바이트: 리드 0xDE~0xE3 + 둘째 0x00~0xE3. idx = 0x1E4 + (리드-0xDE)*228 + 둘째.
  둘째를 E4 미만으로 두는 까닭: 원본 E4 xx 의 둘째는 0xD4 이하라 "E5 이상 = 제어"로 훑는 코드가 있어도 안전.
"""
import collections
import glob
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from gba_extract_strings import parse  # noqa: E402

GBA = ROOT.parent / 'Rockman exe 5' / '_work' / 'exe5-kr' / 'translations' / 'story'
TP = str(ROOT / 'external/TextPet-v1.0.0/TextPet.exe')
PL = ROOT / 'external/textpet-plugins'
JP = re.compile(r'[ぁ-ゖァ-ヺ一-鿿]')
HANGUL = re.compile(r'[가-힣]')
LEAD0 = 0xDE
LEADS = 6
SECOND = 0xE4
IDX_BASE = 0x1E4
SINGLE = list(range(0x0B, 0x67)) + list(range(0x9A, LEAD0))
STRING = re.compile(r'(?ms)^\t"""\n(.*?)\n\t"""$|^\t"((?:[^"\\\n]|\\.|\n(?!\t[a-zA-Z"}]))*)"$')
SCRIPT_SPLIT = re.compile(r'(?m)^(script \d+ (\S+) \{)$')


def load_tm():
    """(번역 메모리 {원문: 번역}, 제외 {원문: 사유}). DS 전용 번역이 GBA 번역을 덮는다."""
    tm, skip = {}, {}
    for f in sorted(glob.glob(str(GBA / 'batch_*.json'))):
        d = json.load(open(f, encoding='utf8'))
        for k, v in d['by_source'].items():
            tm.setdefault(k, v)
    for f in sorted(glob.glob(str(ROOT / 'translations' / 'ds' / '*.json'))):
        d = json.load(open(f, encoding='utf8'))
        tm.update(d.get('by_source', {}))
        skip.update(d.get('skip', {}))
    return tm, skip


def population():
    return json.load(open(ROOT / 'work/population.json', encoding='utf8'))


def tpl_text(name):
    return (ROOT / 'work/tpl' / f'{name}.tpl').read_text(encoding='utf8').replace('\r\n', '\n')


def body_of(m):
    block, single = m.group(1), m.group(2)
    if block is not None:
        return '\n'.join(x[1:] if x.startswith('\t') else x for x in block.split('\n'))
    return single


def substitute(tpl, fn):
    """문자열 상수마다 fn(원문) → 번역(또는 None=그대로). 바꾼 개수를 돌려준다."""
    count = [0]

    def repl(m):
        src = body_of(m)
        new = fn(src)
        if new is None:
            return m.group(0)
        if re.search(r'(?<!\\)"', new):
            raise SystemExit(f'번역문에 큰따옴표: {new!r}')
        count[0] += 1
        return chr(9) + '"%s"' % new
    return STRING.sub(repl, tpl), count[0]


def strings(tpl):
    return [s for _, _, _, s in parse(tpl)]


def assign(freq, keep_chars=''):
    """{글자: 바이트열}. 빈도순으로 1바이트, 나머지 2바이트."""
    order = list(keep_chars) + [c for c, _ in freq.most_common() if c not in keep_chars]
    table = {}
    for c, code in zip(order, SINGLE):
        table[c] = bytes([code])
    rest = order[len(SINGLE):]
    if len(rest) > LEADS * SECOND:
        raise SystemExit(f'음절이 코드 칸을 넘음: {len(order)}')
    for i, c in enumerate(rest):
        table[c] = bytes([LEAD0 + i // SECOND, i % SECOND])
    return table


def glyph_index(code):
    """코드 바이트열 → 글리프 번호."""
    if len(code) == 1:
        return code[0]
    return IDX_BASE + (code[0] - LEAD0) * SECOND + code[1]


def write_tbl(table, keep_jp=()):
    """exe5ds 표에서 가나·한자를 빼고 한글을 넣은 TextPet 표와 게임 정의를 만든다."""
    src = (PL / 'exe5ds-utf8.tbl').read_text(encoding='utf8').replace('\r\n', '\n')
    out = []
    used = {c.hex().upper() for c in table.values()}
    for line in src.split('\n'):
        m = re.fullmatch(r'([0-9A-F]+)=(.*)', line)
        if m and (JP.search(m.group(2)) or m.group(1) in used) and m.group(2) not in keep_jp:
            continue
        out.append(line)
    for c, code in table.items():
        out.append(f'{code.hex().upper()}={c}')
    (PL / 'exe5dsko-utf8.tbl').write_text('\n'.join(out) + '\n', encoding='utf8')
    ini = (PL / 'games.ini').read_text(encoding='utf8')
    if 'name = exe5dsko' not in ini:
        ini = ini.rstrip() + ('\n\n[Game]\nname = exe5dsko\nfull = Rockman EXE 5 DS Korean\n'
                              'cdbs = mmbn5s,mmbn5ds\ntblf = exe5dsko-utf8\n'
                              'vals = mmbn-jump,mmbn-code,mmbn5-mugshots\n')
        (PL / 'games.ini').write_text(ini, encoding='utf8')


def textpet(game, src, sf, dst, df):
    return subprocess.run([TP, 'silent', 'load-plugins', str(PL) + chr(92), 'game', game,
                           'read-text-archives', str(src) + chr(92), '-f', sf,
                           'write-text-archives', str(dst) + chr(92), '-f', df],
                          capture_output=True, text=True, encoding='utf-8', errors='replace')


def classify():
    """아카이브별 일본어 문자열·번역 상태. 번역 0개면서 짧은 조각뿐이면 잡음 후보."""
    tm, skip = load_tm()
    rows = {}
    for n in population():
        ss = [s for s in strings(tpl_text(n)) if JP.search(s)]
        hit = [s for s in ss if s in tm]
        rows[n] = dict(jp=len(ss), hit=len(hit), chars=sum(len(JP.findall(s)) for s in ss),
                       miss=[s for s in ss if s not in tm and s not in skip])
    return rows


if __name__ == '__main__':
    r = classify()
    zero = {n: v for n, v in r.items() if v['jp'] and not v['hit']}
    print('전체', len(r), '일본어 있음', sum(1 for v in r.values() if v['jp']), '번역 0개', len(zero))
    g = collections.Counter()
    for n, v in zero.items():
        g[re.sub(r'[0-9a-f]{2,}.*$', '', n)] += 1
    print(g.most_common(30))
    for n, v in sorted(zero.items(), key=lambda kv: -kv[1]['chars'])[:60]:
        print(n, v['jp'], v['chars'], repr(v['miss'][0][:30]))
