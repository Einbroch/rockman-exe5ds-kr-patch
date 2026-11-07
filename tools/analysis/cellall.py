"""묶음의 모든 셀을 그대로 그린다. 사용법: cellall.py po08 po14 ..."""
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
import ncer  # noqa: E402

items = []
for pre in sys.argv[1:]:
    g = ncer.unpack(f'work/jp/fs/data/rom/dc/{pre}g_lz.bin')
    cs = ncer.cells(ncer.unpack(f'work/jp/fs/data/rom/dc/{pre}c_lz.bin'))
    for i, c in enumerate(cs):
        if c:
            items.append((pre, i, c, g))
cols, cw, ch = 5, 150, 110
H = (len(items) + cols - 1) // cols
im = Image.new('RGB', (cols * cw, H * ch), (20, 20, 40))
dr = ImageDraw.Draw(im)
for k, (n, i, c, g) in enumerate(items):
    bx, by = (k % cols) * cw, (k // cols) * ch
    tmp = Image.new('RGB', (cw, ch - 12), (20, 20, 40))
    x0 = min(p['x'] for p in c)
    y0 = min(p['y'] for p in c)
    ncer.draw(g, c, tmp, -x0, -y0)
    im.paste(tmp, (bx, by + 11))
    dr.text((bx + 1, by), f'{n}.{i}', fill=(255, 255, 0))
    print(n, i, [(p['x'], p['y'], p['w'], p['h'], p['tile'], p['pal']) for p in c][:9])
im.save('work/cs.png')
print(im.size)
