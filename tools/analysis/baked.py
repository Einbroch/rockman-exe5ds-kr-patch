#!/usr/bin/env python3
"""화면들의 OBJ 묶음 중 파일에 구워진 것을 찾아 번호 붙은 목록을 만든다.
입력: work/oam_<이름>.json, work/vram_objA_<이름>.bin (원본 롬으로 뜬 것)
출력: work/baked.json, work/baked.png"""
import collections
import glob
import json
import os
import pathlib
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from scan_msg import lz10  # noqa: E402

names = sys.argv[1:]
files = {}
for f in glob.glob('work/jp/fs/data/rom/dc/*g_lz.bin') + glob.glob('work/jp/fs/data/rom/a/*.bin') + glob.glob('work/jp/fs/data/rom/b/*.bin'):
    d = open(f, 'rb').read()
    x = lz10(d)
    if x:
        files[pathlib.Path(f).as_posix().split('fs/')[1]] = x
print('파일', len(files))
seen = {}
rows = []
for name in names:
    o = json.load(open(f'work/oam_{name}.json'))[os.environ.get('ENG','A')]['oam']
    v = open(f"work/vram_obj{os.environ.get('ENG','A')}_{name}.bin", 'rb').read()
    obs = sorted([r for r in o if not r['d8'] and r['y'] < 192 and r['x'] < 256], key=lambda r: (r['y'], r['x']))
    groups, cur = [], []
    for r in obs:
        if cur and r['y'] == cur[-1]['y'] and r['x'] == cur[-1]['x'] + cur[-1]['w'] and r['pal'] == cur[-1]['pal'] and r['h'] == cur[-1]['h']:
            cur.append(r)
        else:
            if cur:
                groups.append(cur)
            cur = [r]
    if cur:
        groups.append(cur)
    for g in groups:
        tot = sum(r['w'] for r in g)
        h = g[0]['h']
        if tot < 16 or h not in (8, 16):
            continue
        blocks = []
        for r in g:
            n = r['w'] // 8 * (r['h'] // 8) * 32
            blocks.append(v[r['off']:r['off'] + n])
        key = b''.join(blocks)
        if key in seen or len(set(key)) < 3:
            continue
        seen[key] = 1
        found, offs = None, []
        for fn, x in files.items():
            offs = [x.find(b) for b in blocks]
            if all(a >= 0 for a in offs):
                found = fn
                break
        if not found:
            continue
        rows.append(dict(screen=name, x=g[0]['x'], y=g[0]['y'], w=tot, h=h, file=found, offs=offs,
                         objs=[(r['w'], r['h']) for r in g]))
        rows[-1]['img'] = key.hex()
print('구운 묶음', len(rows), collections.Counter(r['file'] for r in rows).most_common(12))
json.dump(rows, open('work/baked.json', 'w'), indent=0)
scale = 2
cols = 4
cw, ch = 190, 38
H = (len(rows) + cols - 1) // cols
im = Image.new('RGB', (cols * cw, H * ch), (30, 30, 50))
dr = ImageDraw.Draw(im)
for i, r in enumerate(rows):
    bx, by = (i % cols) * cw, (i // cols) * ch
    dr.text((bx + 2, by + 1), f"{i} {os.path.basename(r['file'])[:6]} {r['w']}", fill=(255, 255, 0))
    b = bytes.fromhex(r['img'])
    p, xo = 0, 0
    for w, h in r['objs']:
        for ty in range(h // 8):
            for tx in range(w // 8):
                for py in range(8):
                    for px in range(8):
                        q = b[p + (ty * (w // 8) + tx) * 32 + py * 4 + px // 2]
                        c = (q >> (4 * (px & 1))) & 15
                        if c:
                            X, Y = bx + 2 + (xo + tx * 8 + px) * 1, by + 12 + ty * 8 + py
                            if X < bx + cw:
                                im.putpixel((X, Y), (c * 17, c * 17, c * 17))
        p += w // 8 * (h // 8) * 32
        xo += w
im = im.resize((im.width * 2, im.height * 2), 0)
im.save('work/baked.png')
print(im.size)
