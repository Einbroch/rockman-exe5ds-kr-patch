#!/usr/bin/env python3
"""타이틀 로고 한글화. a/title.bin(8bpp 타일)·title00.srn·title00.clt.
옛 글자의 검은 외곽 안쪽을 판으로 칠하고 기울인 굵은 한글을 올린다. 팔레트는 그대로(가까운 색으로 맞춤).
사용법: python tools/gfx_logo.py → work/logo_preview.png (build.py 는 patch 를 부른다)"""
import pathlib
import struct
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = ROOT.parent / '폰트' / 'S-Core_Dream_OTF' / 'SCDream8.otf'
SHEAR = 0.2
# (글자, 왼쪽 x, 아래 y, 폭, 높이, 위 색, 아래 색)
LINES = [
    ('록맨 에그제', 13, 89, 110, 31, (235, 255, 225), (30, 180, 70)),
    ('트윈 리더즈', 66, 106, 132, 16, (255, 235, 110), (235, 60, 30)),
]
# 덮을 판(다각형)
PLATES = [
    [(5, 92), (13, 54), (130, 54), (127, 66), (127, 92)],
    [(60, 108), (64, 91), (127, 91), (134, 86), (211, 82), (204, 108)],
]


def load(data, smap, clt):
    M = struct.unpack('<768H', smap)
    pal = [((v & 31) * 8, ((v >> 5) & 31) * 8, ((v >> 10) & 31) * 8) for v in struct.unpack('<256H', clt)]
    idx = [[0] * 256 for _ in range(192)]
    for i, e in enumerate(M):
        t = e & 1023
        hf, vf = (e >> 10) & 1, (e >> 11) & 1
        for y in range(8):
            for x in range(8):
                idx[(i // 32) * 8 + (7 - y if vf else y)][(i % 32) * 8 + (7 - x if hf else x)] = data[t * 64 + y * 8 + x]
    return idx, pal, M


def plate_mask():
    m = Image.new('L', (256, 192), 0)
    d = ImageDraw.Draw(m)
    for p in PLATES:
        d.polygon(p, fill=255)
    return m


def text_layer(W=256, H=192):
    S = 4
    fill = Image.new('L', (W * S, H * S), 0)
    grad = Image.new('RGB', (W * S, H * S))
    for s, lx, by, tw, th, top, bot in LINES:
        f = ImageFont.truetype(str(FONT), 120)
        l, t, r, b = f.getbbox(s)
        tmp = Image.new('L', (r + 40, b + 40), 0)
        ImageDraw.Draw(tmp).text((20, 20), s, font=f, fill=255)
        tmp = tmp.crop(tmp.getbbox()).resize((tw * S, th * S), Image.LANCZOS)
        sh = int(th * S * SHEAR)
        tmp = tmp.transform((tw * S + sh, th * S), Image.AFFINE, (1, SHEAR, -sh, 0, 1, 0), Image.BICUBIC)
        px, py = lx * S, (by - th) * S
        fill.paste(255, (px, py), tmp)
        for y in range(th * S):
            k = y / max(th * S - 1, 1)
            c = tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3))
            ImageDraw.Draw(grad).rectangle((px - 8, py + y, px + tw * S + sh + 8, py + y), fill=c)
    a = fill.resize((W, H), Image.LANCZOS).point(lambda v: 255 if v > 120 else 0)
    w = a.filter(ImageFilter.MaxFilter(3))
    return a, w, grad.resize((W, H), Image.BILINEAR)


def compose(idx, pal):
    pl = plate_mask()
    edge = pl.filter(ImageFilter.MinFilter(3))
    black = min(range(1, 256), key=lambda i: sum(pal[i]))
    white = max(range(1, 256), key=lambda i: sum(pal[i]))
    a, w, grad = text_layer()
    out = [row[:] for row in idx]
    cache = {}

    def near(c):
        if c not in cache:
            cache[c] = min(range(1, 256), key=lambda i: sum((pal[i][j] - c[j]) ** 2 for j in range(3)))
        return cache[c]
    for y in range(192):
        for x in range(256):
            if pl.getpixel((x, y)):
                out[y][x] = black if edge.getpixel((x, y)) else white
            if a.getpixel((x, y)):
                out[y][x] = near(grad.getpixel((x, y)))
            elif w.getpixel((x, y)) and pl.getpixel((x, y)):
                out[y][x] = white
    return out, pl


def pack(out, M, size):
    """셀을 다시 타일로 묶는다. 뒤집기 없이 같은 타일은 합친다."""
    tiles, index = [], {}
    new = []
    for i in range(768):
        cx, cy = (i % 32) * 8, (i // 32) * 8
        b = bytes(out[cy + y][cx + x] for y in range(8) for x in range(8))
        if b not in index:
            index[b] = len(tiles)
            tiles.append(b)
        new.append(index[b] | (M[i] & 0xF000))
    if len(tiles) * 64 > size:
        raise SystemExit(f'로고 타일 {len(tiles)} > {size // 64}')
    return b''.join(tiles) + bytes(size - len(tiles) * 64), struct.pack('<768H', *new), len(tiles)


def patch(rom):
    ids = {k: rom.filenames.idOf('data/rom/a/' + k) for k in ('title.bin', 'title00.srn', 'title00.clt')}
    data, smap, clt = [bytes(rom.files[ids[k]]) for k in ('title.bin', 'title00.srn', 'title00.clt')]
    idx, pal, M = load(data, smap, clt)
    out, _ = compose(idx, pal)
    c, m, n = pack(out, M, len(data))
    rom.files[ids['title.bin']] = c
    rom.files[ids['title00.srn']] = m
    print('로고 타일', n)


if __name__ == '__main__':
    A = ROOT / 'work/jp/fs/data/rom/a'
    data, smap, clt = [(A / n).read_bytes() for n in ('title.bin', 'title00.srn', 'title00.clt')]
    idx, pal, M = load(data, smap, clt)
    out, pl = compose(idx, pal)
    c, m, n = pack(out, M, len(data))
    print('타일', n)
    im = Image.new('RGB', (256, 192))
    for y in range(192):
        for x in range(256):
            im.putpixel((x, y), pal[out[y][x]])
    im.resize((768, 576), Image.NEAREST).save(ROOT / 'work/logo_preview.png')
