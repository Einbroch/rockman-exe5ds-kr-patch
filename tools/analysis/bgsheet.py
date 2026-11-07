"""db 의 모든 BG 그림을 원본 기준으로 썸네일 시트로: bgsheet.py [조각당 칸수]"""
import os, re, struct, sys
sys.path.insert(0, 'tools')
from scan_msg import lz10
from PIL import Image, ImageDraw
R = 'work/jp/fs/data/rom/db/'
fs = os.listdir(R)
scs = sorted(f[:-10] for f in fs if f.endswith('_sc_lz.bin'))
ths = []
for n in scs:
    base = n if n + '_ch_lz.bin' in fs else None
    if base is None:
        c = [f[:-10] for f in fs if f.endswith('_ch_lz.bin') and f.startswith(n[:-2])]
        if not c:
            c = [f[:-10] for f in fs if f.endswith('_ch_lz.bin') and f[:-10][:-2] == n[:-2]]
        if not c:
            continue
        base = sorted(c)[0]
    ch = lz10(open(R + base + '_ch_lz.bin', 'rb').read())
    sc = lz10(open(R + n + '_sc_lz.bin', 'rb').read())
    plf = R + base + '_pl_lz.bin'
    if not (ch and sc) or not os.path.exists(plf) or ch[:4] != b'RGCN' or sc[:4] != b'RCSN':
        continue
    pl = lz10(open(plf, 'rb').read())
    pal = struct.unpack_from('<256H', pl, 0x28) if len(pl) >= 0x228 else (0,) * 256
    bd = struct.unpack_from('<I', ch, 0x1C)[0]
    b8 = bd == 4
    d = ch[0x30:]
    W = struct.unpack_from('<H', sc, 0x18)[0] // 8
    H = min(struct.unpack_from('<H', sc, 0x1A)[0] // 8, 24)
    m = struct.unpack_from('<%dH' % ((len(sc) - 0x24) // 2), sc, 0x24)
    im = Image.new('RGB', (256, 192))
    for r in range(H):
        for c in range(min(W, 32)):
            e = m[r * W + c]
            t = e & 1023
            for y in range(8):
                for x in range(8):
                    ix = 7 - x if e & 0x400 else x
                    iy = 7 - y if e & 0x800 else y
                    if b8:
                        o = t * 64 + iy * 8 + ix
                        q = d[o] if o < len(d) else 0
                    else:
                        o = t * 32 + iy * 4 + ix // 2
                        q = ((d[o] >> (4 * (ix & 1))) & 15) + (e >> 12) * 16 if o < len(d) else 0
                    w = pal[q & 255]
                    im.putpixel((c * 8 + x, r * 8 + y), ((w & 31) * 8, (w >> 5 & 31) * 8, (w >> 10 & 31) * 8))
    ths.append((n, im))
print(len(ths))
P = 24
for pg in range(0, len(ths), P):
    o = Image.new('RGB', (6 * 262, 4 * 212), 'white')
    dr = ImageDraw.Draw(o)
    for i, (n, im) in enumerate(ths[pg:pg + P]):
        x, y = i % 6 * 262, i // 6 * 212
        o.paste(im, (x, y + 16))
        dr.text((x + 2, y + 2), n, fill='black')
    o.save('work/bgs_%02d.png' % (pg // P))
