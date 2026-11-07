#!/usr/bin/env python3
"""미번역 문자열을 맥락·유사 번역과 함께 묶음 파일로 뽑는다.
출력: work/miss/ms_NNN.txt  (id, 파일, 화자, 원문, 가장 비슷한 GBA 원문·번역)
"""
import collections
import difflib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import kotext  # noqa: E402
from kotext import JP, parse  # noqa: E402
import build  # noqa: E402

BATCH = int(sys.argv[1]) if len(sys.argv) > 1 else 150


def main():
    tm, skip = kotext.load_tm()
    pop = kotext.population()
    where = collections.defaultdict(list)
    for n in pop:
        if build.NOISE.search(n) or not pop[n]['rt']:
            continue
        t = kotext.tpl_text(n)
        for sc, db, sp, s in parse(t):
            if JP.search(s) and s not in tm and s not in skip:
                where[s].append((n, sc, sp))
    keys = list(tm)
    by_len = collections.defaultdict(list)
    for k in keys:
        by_len[len(k) // 8].append(k)

    def similar(s):
        cand = []
        for b in range(len(s) // 8 - 1, len(s) // 8 + 2):
            cand += by_len.get(b, [])
        m = difflib.get_close_matches(s, cand, n=1, cutoff=0.6)
        return m[0] if m else None
    rows = []
    for s, w in where.items():
        rows.append(dict(src=s, where=w[:3], n=len(w)))
    # 같은 아카이브끼리 원래 순서로
    order = {n: i for i, n in enumerate(pop)}
    rows.sort(key=lambda r: (order[r['where'][0][0]], r['where'][0][1]))
    out = ROOT / 'work/miss'
    out.mkdir(exist_ok=True)
    for f in out.glob('*'):
        f.unlink()
    print('미번역', len(rows), '글자', sum(len(JP.findall(r['src'])) for r in rows))
    for i, r in enumerate(rows):
        r['id'] = i
        sim = similar(r['src'])
        if sim:
            r['sim'] = sim
            r['simko'] = tm[sim]
    json.dump(rows, open(ROOT / 'work/miss.json', 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    g = collections.Counter()
    for r in rows:
        g[re.sub(r'[0-9a-f]{2,}.*$', '', r['where'][0][0])] += 1
    print(g.most_common(40))


if __name__ == '__main__':
    main()
