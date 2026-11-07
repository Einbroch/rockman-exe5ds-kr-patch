#!/usr/bin/env python3
"""NNS NCER(RECN)/NCGR(RGCN) 읽기. 셀 = OAM 조각 목록."""
import struct
import sys

sys.path.insert(0, 'tools')
from scan_msg import lz10  # noqa: E402

SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


def unpack(path):
    d = open(path, 'rb').read()
    return lz10(d) or d


def cells(d):
    """[셀] 각 셀 = [dict(x,y,w,h,tile(32바이트 단위),pal)]"""
    if d[:4] != b'RECN':
        raise ValueError('RECN 아님')
    n, bank, off, mapping = struct.unpack_from('<HHII', d, 0x18)
    base = 0x18 + off
    esz = 16 if bank == 1 else 8
    oam0 = base + n * esz
    shift = mapping & 7
    out = []
    for i in range(n):
        cnt, attr, oo = struct.unpack_from('<HHI', d, base + i * esz)
        parts = []
        for k in range(cnt):
            a0, a1, a2 = struct.unpack_from('<HHH', d, oam0 + oo + k * 6)
            y = a0 & 255
            y = y - 256 if y >= 128 else y
            x = a1 & 511
            x = x - 512 if x >= 256 else x
            w, h = SIZES[(a0 >> 14, a1 >> 14)]
            parts.append(dict(x=x, y=y, w=w, h=h, tile=(a2 & 1023) << shift, pal=a2 >> 12, d8=bool(a0 & 0x2000)))
        out.append(parts)
    return out


def char_offset(g):
    """NCGR 타일 데이터 시작."""
    if g[:4] != b'RGCN':
        raise ValueError('RGCN 아님')
    size = struct.unpack_from('<I', g, 0x10 + 4)[0]
    return 0x10 + struct.unpack_from('<I', g, 0x10 + 0x18)[0] + 0 if False else 0x30


def draw(g, cell, im, ox, oy, base=0x30):
    for p in cell:
        if p['d8']:
            continue
        o = base + p['tile'] * 32
        tw = p['w'] // 8
        for ty in range(p['h'] // 8):
            for tx in range(tw):
                t = o + (ty * tw + tx) * 32
                if t + 32 > len(g):
                    continue
                for py in range(8):
                    for px in range(8):
                        q = g[t + py * 4 + px // 2]
                        c = (q >> (4 * (px & 1))) & 15
                        if c:
                            X, Y = ox + p['x'] + tx * 8 + px, oy + p['y'] + ty * 8 + py
                            if 0 <= X < im.width and 0 <= Y < im.height:
                                im.putpixel((X, Y), (c * 17, c * 17, c * 17))
