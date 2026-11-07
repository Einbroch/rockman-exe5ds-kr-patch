"""여러 줄 셀의 글자 줄을 조각(part) 단위로 보여 준다: 파일.셀.줄y"""
import glob
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
import ncer  # noqa: E402

items = []
seen = set()
for f in sorted(glob.glob('work/jp/fs/data/rom/dc/[pw]o*g_lz.bin')):
    c = f.replace('g_lz', 'c_lz')
    if not os.path.exists(c):
        continue
    g = ncer.unpack(f)
    cs = ncer.cells(ncer.unpack(c))
    for i, cell in enumerate(cs):
        ys = [p['y'] for p in cell] + [p['y'] + p['h'] for p in cell]
        if not cell or max(ys) - min(ys) <= 16:
            continue
        rows = {}
        for p in cell:
            if p['h'] <= 16 and p['w'] <= 64:
                rows.setdefault(p['y'], []).append(p)
        for y, ps in rows.items():
            xs = [p['x'] for p in ps] + [p['x'] + p['w'] for p in ps]
            w = max(xs) - min(xs)
            if w < 24 or w > 112:
                continue
            key = tuple(sorted((p['tile'], p['w'], p['h']) for p in ps))
            if key in seen:
                continue
            ink = 0
            for p in ps:
                o = 0x30 + p['tile'] * 32
                ink += sum(1 for b in g[o:o + p['w'] * p['h'] // 2] if b)
            if ink < 12 or ink > (w * 16 // 2) * 0.8:
                continue
            seen.add(key)
            items.append((os.path.basename(f)[:4], i, y, ps, g, min(xs), w))
print(len(items))
cols, cw, ch = 7, 118, 30
H = (len(items) + cols - 1) // cols
im = Image.new('RGB', (cols * cw, H * ch), (20, 20, 40))
dr = ImageDraw.Draw(im)
for k, (n, i, y, ps, g, x0, w) in enumerate(items):
    bx, by = (k % cols) * cw, (k // cols) * ch
    dr.text((bx + 1, by), f'{n}.{i}.{y}', fill=(255, 255, 0))
    ncer.draw(g, ps, im, bx + 1 - x0, by + 11 - y)
im = im.resize((im.width * 2, im.height * 2), 0)
if im.height > 1500:
    im = im.crop((0, 0, im.width, 1500))
im.save('work/cs.png')
print(im.size)
