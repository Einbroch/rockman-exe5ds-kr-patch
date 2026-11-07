import glob
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from scan_msg import lz10  # noqa: E402

files = sorted(glob.glob('work/jp/fs/data/rom/dc/po*g_lz.bin'))
print(len(files), [os.path.basename(f)[:4] + ':' + str(len(lz10(open(f, 'rb').read())) // 32) for f in files])
a, b = int(sys.argv[1]), int(sys.argv[2])
col = 30
rows = []
for f in files[a:b]:
    x = lz10(open(f, 'rb').read())[0x30:]
    n = len(x) // 32 // 8      # 4×2 묶음
    r = (n + col - 1) // col
    im = Image.new('L', (col * 33, r * 17 + 10), 40)
    ImageDraw.Draw(im).text((0, 0), os.path.basename(f), fill=255)
    for k in range(n):
        for t in range(8):
            i = k * 8 + t
            for y in range(8):
                for xx in range(8):
                    q = x[i * 32 + y * 4 + xx // 2]
                    v = (q >> (4 * (xx & 1))) & 15
                    im.putpixel(((k % col) * 33 + (t % 4) * 8 + xx, 10 + (k // col) * 17 + (t // 4) * 8 + y), (v * 17 if v else 0))
    rows.append(im)
H = sum(i.height for i in rows)
o = Image.new('L', (col * 33, H), 0)
y = 0
for i in rows:
    o.paste(i, (0, y))
    y += i.height
o=o.resize((o.width*3//2,o.height*3//2),0);o.save('work/t.png')
print(o.size)
