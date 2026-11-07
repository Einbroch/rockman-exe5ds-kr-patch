import json, re, collections, os
pop = json.load(open('work/population.json', encoding='utf8'))
G = collections.defaultdict(list)
for n, v in pop.items():
    m = re.match(r'a_(st|rt|dm)[0-9a-f]{4}(?:_([a-z]))?', n)
    k = (m.group(1) + '_' + (m.group(2) or '')) if m else 'other'
    p = f'work/ko_msg/{n}.msg'
    new = os.path.getsize(p) if os.path.exists(p) else v['size']
    G[k].append((v['size'], new, n))
for k, L in sorted(G.items()):
    print(k, len(L), '원본 최대', max(x[0] for x in L), '번역 최대', max(x[1] for x in L), '넘는 것',
          [(x[2], x[0], x[1]) for x in L if x[1] > max(y[0] for y in L)][:5])
