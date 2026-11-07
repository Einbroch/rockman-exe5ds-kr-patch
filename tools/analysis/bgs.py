"""db/ BG 전부 또는 지정 BG 를 그린다. 사용법: bgs.py (전체 축소) / bgs.py bg0600 bg1400"""
import glob
import os
import struct
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
import ncer  # noqa: E402

B = 'work/jp/fs/data/rom/db/'


def render(n):
    c = ncer.unpack(B + n + '_ch_lz.bin')
    s = ncer.unpack(B + n + '_sc_lz.bin')
    m = struct.unpack_from('<1024H', s, 0x24)
    im = Image.new('L', (256, 256))
    for i, e in enumerate(m):
        t = e & 1023
        hf, vf = (e >> 10) & 1, (e >> 11) & 1
        o = 0x30 + t * 64
        if o + 64 > len(c):
            continue
        for y in range(8):
            for x in range(8):
                v = c[o + y * 8 + x] // 17
                X = (i % 32) * 8 + (7 - x if hf else x)
                Y = (i // 32) * 8 + (7 - y if vf else y)
                im.putpixel((X, Y), v * 17)
    return im


if len(sys.argv) > 1:
    W = 2
    o = Image.new('L', (len(sys.argv[1:]) * 256 * W // 1, 192 * W))
    for i, n in enumerate(sys.argv[1:]):
        o.paste(render(n).crop((0, 0, 256, 192)).resize((256 * W, 192 * W), 0), (i * 256 * W, 0))
    o.save('work/t.png')
else:
    names = sorted(os.path.basename(f).split('_')[0] for f in glob.glob(B + (os.environ.get('PRE', 'bg')) + '*_sc_lz.bin'))
    cols = 9
    o = Image.new('L', (cols * 172, ((len(names) + cols - 1) // cols) * 142), 0)
    d = ImageDraw.Draw(o)
    for i, n in enumerate(names):
        try:
            q = render(n)
        except OSError:
            continue
        a = q.crop((0, 0, 256, 192)).resize((170, 128))
        o.paste(a, ((i % cols) * 172, (i // cols) * 142 + 12))
        d.text(((i % cols) * 172, (i // cols) * 142), n, fill=255)
    o.save('work/t.png')
    print(o.size)
