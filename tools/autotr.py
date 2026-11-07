#!/usr/bin/env python3
"""규칙으로 조립되는 DS 전용 문자열을 번역한다. 결과: translations/ds/000_auto.json
- chipinf2/3: 「이름」+본문. 이름은 칩 이름표, 본문은 같은 번호의 chipinf0/1 번역을 2줄로 합침.
- 게시판 P.A 조합: ' 캐논A|+캐논B|+캐논C'.
- 「이름」 한 줄: P.A 이름.
조립한 것은 사람이 한 번 훑도록 work/auto_review.txt 로도 낸다.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kotext  # noqa: E402
from kotext import JP, parse  # noqa: E402

NL = chr(10)


def scripts(name):
    """{스크립트 번호: 첫 문자열}"""
    out = {}
    for sc, db, sp, s in parse(kotext.tpl_text(name)):
        out.setdefault(sc, s)
    return out


def main():
    tm, skip = kotext.load_tm()
    auto_f = ROOT / 'translations/ds/000_auto.json'
    names = {}
    for a in ('a_chipname0', 'a_chipname1'):
        for s in scripts(a).values():
            if s in tm:
                names[s.strip()] = tm[s].strip()
    # 번호가 있는 기본형 등 이름표 밖의 것도 번역 메모리에서 찾는다
    for k, v in tm.items():
        if NL not in k and len(k) < 14 and JP.search(k):
            names.setdefault(k.strip(), v.strip())
    src = json.load(open(ROOT / 'translations/ds_src.json', encoding='utf8'))
    by, review, left = {}, [], []
    srcset = {r['src'] for r in src}
    limits = {}
    for inf2, inf0 in (('a_chipinf2', 'a_chipinf0'), ('a_chipinf3', 'a_chipinf1')):
        a, b = scripts(inf2), scripts(inf0)
        for i, s in a.items():
            if s not in srcset:
                continue
            lines = s.split(NL)
            head = lines[0]
            m = re.fullmatch('「(.*)」', head)
            ko_body = tm.get(b.get(i))
            if not m or m.group(1) not in names or not ko_body:
                left.append(s)
                continue
            ko = ko_body.split(NL)
            width = 18
            # 원문 줄 수만큼으로 합친다
            want = len(lines) - 1
            joined = []
            cur = ''
            for part in ko:
                t = (cur + ' ' + part).strip() if cur else part
                if len(t) <= width and (len(joined) >= want - 1 or len(t) <= width - 4):
                    cur = t
                else:
                    joined.append(cur)
                    cur = part
            joined.append(cur)
            if len(joined) > want:
                left.append(s)
                continue
            by[s] = NL.join([f'「{names[m.group(1)]}」'] + joined)
    # 게시판 조합
    pat = re.compile(r'^(.+?) ?([A-Z*])$')

    def chip(x):
        x = x.strip().lstrip('+').strip()
        m = pat.match(x)
        if not m:
            return None
        n = m.group(1).strip()
        return names[n] + m.group(2) if n in names else None
    for r in src:
        s = r['src']
        if s in by:
            continue
        if NL in s and all(ln.strip().startswith('+') or i == 0 for i, ln in enumerate(s.split(NL))):
            parts = [chip(ln) for ln in s.split(NL)]
            if all(parts):
                by[s] = ' ' + (NL + '+').join(parts)
                continue
        m = re.fullmatch('「(.*)」', s)
        if m and m.group(1) in names:
            by[s] = f'「{names[m.group(1)]}」'
    json.dump({'by_source': by}, open(auto_f, 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    with open(ROOT / 'work/auto_review.txt', 'w', encoding='utf8') as f:
        for k, v in by.items():
            f.write(k.replace(NL, '|') + chr(9) + v.replace(NL, '|') + NL)
    print('자동', len(by), '본문 못 맞춤', len(left), '남은', len(src) - len(by))
    cells = [len(x) for k in by for x in by[k].split(NL)]
    print('최장 줄(글자수)', max(cells))


if __name__ == '__main__':
    main()
