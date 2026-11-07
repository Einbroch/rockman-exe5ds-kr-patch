#!/usr/bin/env python3
"""PET 메뉴 라벨(dc/po01g_lz.bin) 한글화.
work/oam_menu.json(원본 메뉴 화면의 OAM)에서 라벨을 이루는 OBJ 줄을 찾아 그 타일 칸에 그린다.
라벨은 흰 글자(F)에 어두운 외곽(E), 타일은 OBJ 1D(32×16 등).
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from lz import compress  # noqa: E402
from scan_msg import lz10  # noqa: E402

LABELS = {(20, 42): '칩 폴더', (108, 42): '넷내비', (188, 42): '통신',
          (28, 90): '서브칩', (108, 90): 'E메일', (188, 90): '맵',
          (12, 138): '라이브러리', (108, 138): '키 아이템', (188, 138): '세이브'}
INK, EDGE = 0xF, 0xE


def text_mask(s):
    """8×16 칸 글리프 줄 → {(x,y)}, 폭. 가나와 같은 8px 칸."""
    import build
    import exe1k_hangul
    src = exe1k_hangul.load(build.EXE1K)
    a9 = (ROOT / 'work/jp/arm9.bin').read_bytes()
    px, x = set(), 0
    for c in s:
        if c == ' ':
            x += 4
            continue
        if c == 'E':
            cell = a9[0x119784 + 0xE8 * 0x40:0x119784 + 0xE9 * 0x40]
            ink = {(i % 2 * 1 + (i // 4 % 1), 0) for i in ()}
            ink = set()
            for y in range(16):
                for xx in range(8):
                    if (cell[y * 4 + xx // 2] >> (4 * (xx & 1))) & 15 == 1:
                        ink.add((xx, y))
        else:
            ink = build.ink8(src, c)
        px |= {(x + a, b) for a, b in ink}
        x += 8
    return px, x - 1


def spans(oam):
    """같은 줄 이어진 OBJ 를 라벨 묶음으로."""
    rows = sorted([r for r in oam if r['pal'] == 2 and r['h'] == 16], key=lambda r: (r['y'], r['x']))
    groups, cur = [], []
    for r in rows:
        if cur and r['y'] == cur[-1]['y'] and r['x'] == cur[-1]['x'] + cur[-1]['w']:
            cur.append(r)
        else:
            if cur:
                groups.append(cur)
            cur = [r]
    if cur:
        groups.append(cur)
    return [g for g in groups if g[0]['y'] != 32]


def patch(data, vram):
    x = bytearray(lz10(data))
    oam = json.load(open(ROOT / 'ref/oam_menu.json'))['A']['oam']
    probe = vram[0x4000 + 0x10:0x4000 + 0x30]
    at = bytes(x).find(probe)
    if at < 0:
        raise SystemExit('po01g 위치 못 찾음')
    delta = at - 0x4010
    done = 0
    for g in spans(oam):
        key = (g[0]['x'], g[0]['y'])
        text = None
        for (kx, ky), s in LABELS.items():
            if ky == key[1] and abs(kx - key[0]) <= 16:
                text = s
        if text is None:
            continue
        width = sum(r['w'] for r in g)
        canvas = [[0] * width for _ in range(16)]
        px, tw = text_mask(text)
        if tw > width:
            raise SystemExit(f'{text}: 폭 {tw} > {width}')
        ox, oy = (width - tw) // 2, 0
        for a, b in px:
            canvas[b + oy][a + ox] = INK
        for a, b in px:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    X, Y = a + ox + dx, b + oy + dy
                    if 0 <= X < width and 0 <= Y < 16 and canvas[Y][X] == 0:
                        canvas[Y][X] = EDGE
        bx = 0
        for r in g:
            tw_, th_ = r['w'] // 8, r['h'] // 8
            base = r['off'] + delta
            for ty in range(th_):
                for tx in range(tw_):
                    o = base + (ty * tw_ + tx) * 32
                    if o < 0 or o + 32 > len(x):
                        raise SystemExit('타일 범위 밖')
                    for py in range(8):
                        for pxx in range(0, 8, 2):
                            cx = bx + tx * 8 + pxx
                            cy = ty * 8 + py
                            x[o + py * 4 + pxx // 2] = canvas[cy][cx] | canvas[cy][cx + 1] << 4
            bx += r['w']
        done += 1
    if done != len(LABELS):
        raise SystemExit(f'라벨 {done}/{len(LABELS)}')
    return compress(bytes(x))
