#!/usr/bin/env python3
"""libe_telop00 스프라이트: 해제본 앞 4바이트 + 머리 0x20 + 타일 0x1600 + 프레임.
프레임 표 = F(0x16F0)+4 부터 u32 오프셋 11개(F 기준), 항목 5바이트(타일, x, y, 크기|뒤집기, 모양), FF 끝."""
import struct
import sys

sys.path.insert(0, 'tools')
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
F = 0x16F0
TILES = 0x20


def frames(x):
    """x = 앞 4바이트 뺀 해제본. [[dict(t,x,y,w,h,hf,vf)]]"""
    out = []
    offs = struct.unpack_from('<11I', x, F + 4)
    for o in offs:
        p = F + 4 + o
        items = []
        while x[p] != 0xFF and p + 5 <= len(x):
            t, px, py, sz, sh = x[p:p + 5]
            px = px - 256 if px > 127 else px
            py = py - 256 if py > 127 else py
            w, h = SIZES[(sh & 3, sz & 3)]
            items.append(dict(t=t, x=px, y=py, w=w, h=h, hf=(sz >> 6) & 1, vf=(sz >> 7) & 1, pal=sh >> 4))
            p += 5
        out.append(items)
    return out


if __name__ == '__main__':
    from PIL import Image, ImageDraw
    from scan_msg import lz10
    x = lz10(open('work/jp/fs/data/rom/a/libe_telop00_bin_lz.bin', 'rb').read())[4:]
    fs = frames(x)
    o = Image.new('L', (520, 11 * 62), 30)
    d = ImageDraw.Draw(o)
    for k, f in enumerate(fs):
        d.text((0, k * 62), str(k), fill=255)
        for it in f:
            tw = it['w'] // 8
            for ty in range(it['h'] // 8):
                for tx in range(tw):
                    t = TILES + (it['t'] + ty * tw + tx) * 32
                    if t + 32 > len(x):
                        continue
                    for py in range(8):
                        for px in range(8):
                            q = x[t + py * 4 + px // 2]
                            v = (q >> (4 * (px & 1))) & 15
                            if v:
                                X = it['x'] + (it['w'] - 1 - (tx * 8 + px) if it['hf'] else tx * 8 + px)
                                Y = it['y'] + (it['h'] - 1 - (ty * 8 + py) if it['vf'] else ty * 8 + py)
                                o.putpixel((256 + X, k * 62 + 30 + Y), v * 17)
    o.save('work/t.png')
    print(o.size, [len(f) for f in fs])
