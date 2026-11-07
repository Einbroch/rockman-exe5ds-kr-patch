#!/usr/bin/env python3
"""번역문 폭·줄 수 전수 검사. 한글 12px, 빈칸 8px, 나머지 11px.
기준은 스크립트마다 원문에서 잰다: 원문 줄(11px/8px)과 대사창 180px 중 큰 값.
메뉴 DB(mmbn5s) 는 칸 수(8px)로 원문 최장 줄과 비교."""
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kotext  # noqa: E402
from kotext import parse  # noqa: E402

NL = chr(10)
BS = chr(92)


def px(s):
    return sum(12 if '가' <= c <= '힣' else 8 if c == ' ' else 11 for c in s)


def lines(s):
    return s.replace(BS + 'n', NL).split(NL)


def clean(s):
    return re.sub(r'\[[^\]]*\]', 'W', s).replace(BS + '"', '"')


def main():
    bad = collections.defaultdict(list)
    tot = 0
    for f in sorted((ROOT / 'work/ko_tpl').glob('*.tpl')):
        n = f.stem
        ko = list(parse(f.read_text(encoding='utf8')))
        jp = list(parse(kotext.tpl_text(n)))
        if len(ko) != len(jp):
            bad['개수'].append((n, len(jp), len(ko)))
            continue
        wmax = max((px(x) for *_, s in jp for x in lines(clean(s))), default=0)
        cmax = max((len(x) for *_, s in jp for x in lines(clean(s))), default=0)
        for (sc, db, sp, a), (_, _, _, b) in zip(jp, ko):
            tot += 1
            la, lb = lines(clean(a)), lines(clean(b))
            if len(lb) > max(len(la), 3):
                bad['줄 수'].append((n, sc, b[:40]))
            if db == 'mmbn5s':
                for x in lb:
                    if len(x) > cmax:
                        bad['메뉴 칸'].append((n, sc, cmax, len(x), x))
            else:
                lim = max(wmax, 180)
                for x in lb:
                    if px(x) > lim:
                        bad['대사 폭'].append((n, sc, lim, px(x), x))
    print('문자열', tot, {k: len(v) for k, v in bad.items()})
    json.dump(bad, open(ROOT / 'work/gate_width.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    for k, v in bad.items():
        print('==', k)
        for r in v[:40]:
            print(r)


if __name__ == '__main__':
    main()
