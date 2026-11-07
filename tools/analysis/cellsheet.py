"""po/wo 셀 전수 시트. 사용법: cellsheet.py 접두어들 → work/cs.png
폭 96 이하·높이 16 이하이고 잉크가 글자처럼 조밀한 셀만 추린다."""
import glob
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
import ncer  # noqa: E402

items = []
for pre in sys.argv[1:]:
    for f in sorted(glob.glob(f'work/jp/fs/data/rom/dc/{pre}*g_lz.bin')):
        c = f.replace('g_lz', 'c_lz')
        if not os.path.exists(c):
            continue
        g = ncer.unpack(f)
        try:
            cs = ncer.cells(ncer.unpack(c))
        except Exception as e:
            print(f, e)
            continue
        seen = set()
        for i, cell in enumerate(cs):
            if not cell:
                continue
            xs = [p['x'] for p in cell] + [p['x'] + p['w'] for p in cell]
            ys = [p['y'] for p in cell] + [p['y'] + p['h'] for p in cell]
            w, h = max(xs) - min(xs), max(ys) - min(ys)
            if w > 100 or h > 16 or w < 16 or h < 8:
                continue
            key = tuple((p['tile'], p['w'], p['h']) for p in cell)
            if key in seen:
                continue
            seen.add(key)
            items.append((os.path.basename(f)[:4], i, cell, g, min(xs), min(ys), w, h))
print(len(items))
cols, cw, ch = 7, 112, 30
H = (len(items) + cols - 1) // cols
im = Image.new('RGB', (cols * cw, H * ch), (20, 20, 40))
dr = ImageDraw.Draw(im)
for k, (n, i, cell, g, x0, y0, w, h) in enumerate(items):
    bx, by = (k % cols) * cw, (k // cols) * ch
    dr.text((bx + 1, by), f'{n}.{i}', fill=(255, 255, 0))
    ncer.draw(g, cell, im, bx + 1 - x0, by + 11 - y0)
im = im.resize((im.width * 2, im.height * 2), 0)
im.save('work/cs.png')
print(im.size)
