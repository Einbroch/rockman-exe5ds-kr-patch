#!/usr/bin/env python3
"""translations/ds/NNN.tsv(id<TAB>번역, | = 줄바꿈, #SKIP 사유) → NNN.json, 줄 수·길이 검사."""
import glob
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from kotext import HANGUL, JP  # noqa: E402

rows = {r['id']: r for r in json.load(open(ROOT / 'translations/ds_src.json', encoding='utf8'))}
NL = chr(10)
bad = 0
total = 0
for f in sorted(glob.glob(str(ROOT / 'translations/ds/*.tsv'))):
    by, skip = {}, {}
    for ln in open(f, encoding='utf8'):
        ln = ln.rstrip('\r\n')
        if not ln or ln.startswith('#'):
            continue
        i, ko = ln.split('\t', 1)
        i = int(i)
        src = rows[i]['src']
        if ko.startswith('#SKIP'):
            skip[src] = ko
            continue
        ko = ko.replace('|', NL)
        if JP.search(ko):
            print('일본어 남음', i, ko)
            bad += 1
        a, b = src.split(NL), ko.split(NL)
        if len(a) != len(b) and not rows[i].get('free'):
            print('줄 수 다름', i, len(a), len(b), ko.replace(NL, '|'))
            bad += 1
        for x, y in zip(sum((q.split(chr(92) + 'n') for q in a), []), sum((q.split(chr(92) + 'n') for q in b), [])):
            # 한글 12px, 라틴 등 11px 로 어림. 원문 줄이 짧아도 대사창 15자는 허용
            if len(y) > max(len(x), 15) + 1:
                print('긴 줄', i, len(x), len(y), y)
                bad += 1
        by[src] = ko
        total += 1
    json.dump({'by_source': by, 'skip': skip}, open(f[:-4] + '.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
print('항목', total, '문제', bad)
