#!/usr/bin/env python3
"""미번역 묶음 보기. 사용법: showmiss.py 시작 개수"""
import difflib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
rows = json.load(open(ROOT / 'translations/ds_src.json', encoding='utf8'))
sys.path.insert(0, str(ROOT / 'tools'))
import kotext  # noqa: E402
tm, skip = kotext.load_tm()
rows = [r for r in rows if r['src'] not in tm and r['src'] not in skip]
print('남은', len(rows))
a, n = int(sys.argv[1]), int(sys.argv[2])
last = None
for r in rows[a:a + n]:
    w = r['where'][0]
    if w[0] != last:
        print(f'## {w[0]}')
        last = w[0]
    s = r['src'].replace('\n', '|')
    sp = w[2] or ''
    line = f"{r['id']}\t{sp}\t{s}"
    if 'sim' in r:
        ratio = difflib.SequenceMatcher(None, r['src'], r['sim']).ratio()
        if ratio >= 0.7:
            line += f"\t~{r['simko'].replace(chr(10), '|')}"
    print(line)
