#!/usr/bin/env python3
"""통신 이름 입력 자판(a/collabo.msg 스크립트 40~47 + db/wbg0100·wbg0101).

칸 표는 쪽마다 60바이트(왼쪽 묶음 5×6, 오른쪽 묶음 5×6)이고 고른 칸의 바이트가 그대로 이름에 들어간다.
그래서 자판 글자는 전부 1바이트 코드여야 한다. KEEP 은 1바이트 배정을 강제한다.
그림은 8bpp 한 장(타일 최대 512칸, BG2 0xC000~0x14000)이고 쪽 전환은 맵만 바꾼다.
"""
import struct

from lz import compress
from scan_msg import lz10

NAMES = '김박최강윤임권황송류홍양손백허남심노곽차민엄채원천현영철호재준훈석태동혁빈연희경선숙혜'
OTHERS = '가고구기나다대도라로리마문미바방배보부비사상서성소수시신아오우유은이인자장전정제조주지진하한해'
KEEP = ''.join(sorted(set(NAMES + OTHERS)))
assert len(KEEP) == 90, len(KEEP)
PAGE = [KEEP[:45], KEEP[45:]]
EXTRA = ['0123456789-!?. ', ' ' * 15]
WORDS = [['다음쪽', '앞으로', '뒤로', '결정', '취소'], ['앞쪽', '앞으로', '뒤로', '결정', '취소']]
ASCII = {'0': 1, '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10,
         '-': 0x79, '!': 0x83, '?': 0x7E, '.': 0x89, '~': 0x8E, ' ': 0}


def page_bytes(p, table):
    out = bytearray()
    for c in PAGE[p] + EXTRA[p]:
        out += table[c] if c in table else bytes([ASCII[c]])
    if len(out) != 60:
        raise SystemExit('자판 칸 표 길이가 60이 아니다')
    return bytes(out)


def patch_tables(msg, table):
    """스크립트 40~47 칸 표. 짝수는 앞쪽, 홀수는 뒤쪽 자판."""
    n = struct.unpack_from('<H', msg)[0] // 2
    off = list(struct.unpack_from(f'<{n}H', msg)) + [len(msg)]
    out = bytearray(msg)
    for i in range(40, 48):
        if off[i + 1] - off[i] != 61:
            raise SystemExit(f'칸 표 {i} 길이 {off[i + 1] - off[i]}')
        out[off[i]:off[i] + 60] = page_bytes(i & 1, table)
    return bytes(out)


def patch_overlay(rom, table):
    """오버레이 416 의 실제 칸 표: 60바이트 6벌(쪽 2 × ゛ 없음·있음·゜), 행마다 왼쪽 5칸 + 오른쪽 5칸, 끝칸은 0."""
    ov = rom.loadArm9Overlays()[416]
    d = bytearray(rom.files[ov.fileID])
    o = d.find(bytes.fromhex('9e9f9d9b9cbdbbbab9bccecfcccbcdc0bebf828e'))
    if o < 0:
        raise SystemExit('자판 칸 표를 못 찾았다')
    for n in range(6):
        src = page_bytes(n & 1, table)
        row = bytearray(60)
        for i in range(60):
            b, k = (0, i) if i < 30 else (5, i - 30)
            row[(k // 5) * 10 + b + k % 5] = src[i]
        if row[59] or d[o + n * 60 + 59]:
            raise SystemExit('자판 표 끝칸')
        d[o + n * 60:o + (n + 1) * 60] = row
    rom.files[ov.fileID] = bytes(d)


def lum(c):
    return (c & 31) * 3 + (c >> 5 & 31) * 6 + (c >> 10 & 31)


def decode(ch, m):
    px = [[0] * 256 for _ in range(256)]
    for i, e in enumerate(m):
        t = e & 1023
        for y in range(8):
            for x in range(8):
                ix = 7 - x if e & 0x400 else x
                iy = 7 - y if e & 0x800 else y
                px[(i // 32) * 8 + y][(i % 32) * 8 + x] = ch[t * 64 + iy * 8 + ix]
    return px


def encode(pages):
    """모든 쪽을 타일로 다시 자른다. 뒤집기 재사용 포함."""
    seen = {bytes(64): 0}
    tiles = [bytes(64)]
    maps = []
    for px in pages:
        m = []
        for r in range(32):
            for c in range(32):
                t = bytes(px[r * 8 + y][c * 8 + x] for y in range(8) for x in range(8))
                hit = None
                for flag, v in ((0, t),
                                (0x400, bytes(t[y * 8 + 7 - x] for y in range(8) for x in range(8))),
                                (0x800, bytes(t[(7 - y) * 8 + x] for y in range(8) for x in range(8))),
                                (0xC00, bytes(t[(7 - y) * 8 + 7 - x] for y in range(8) for x in range(8)))):
                    if v in seen:
                        hit = seen[v] | flag
                        break
                if hit is None:
                    seen[t] = len(tiles)
                    hit = len(tiles)
                    tiles.append(t)
                m.append(hit)
        maps.append(m)
    return tiles, maps


def dot(px, x, y, v):
    if 0 <= x < 256 and 0 <= y < 256:
        px[y][x] = v


def glyph(px, g, x0, y0, ink, shadow):
    for y, row in enumerate(g):
        for x, b in enumerate(row):
            if b:
                dot(px, x0 + x + 1, y0 + y + 1, shadow)
    for y, row in enumerate(g):
        for x, b in enumerate(row):
            if b:
                dot(px, x0 + x, y0 + y, ink)


def label(px, x0, y0, w, h, mask, tw, pal, shadow=True, left=False, flat=False):
    used = {px[y][x] for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
    ink = max(used, key=lambda v: lum(pal[v]))
    edge = min(used, key=lambda v: lum(pal[v]))
    hist = {}
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            hist[px[y][x]] = hist.get(px[y][x], 0) + 1
    mode = max(hist, key=hist.get)

    def rim(v):                        # 단추 테두리(주황)는 지우지 않는다
        c = pal[v]
        return (c & 31) >= (c >> 10 & 31) + 10
    for y in range(y0, y0 + h):
        if flat:
            mid = x0 + w // 2
            for rng in (range(mid, x0 + w), range(mid - 1, x0 - 1, -1)):
                for x in rng:
                    if rim(px[y][x]):
                        break
                    px[y][x] = mode
            continue
        fill = px[y][x0 - 1 if left else x0 + w]
        for x in range(x0, x0 + w):
            px[y][x] = fill
    ox = x0 + (w - tw) // 2
    if shadow:
        for a, b in mask:
            dot(px, ox + a + 1, y0 + b + 1, edge)
    for a, b in mask:
        dot(px, ox + a, y0 + b, ink)


def white(pal):
    return max(range(1, 256), key=lambda v: lum(pal[v]))


def black(pal):
    return min(range(1, 256), key=lambda v: lum(pal[v]))


def soft_erase(px, x0, y0, w, h, pal):
    """밝은 글자와 그림자만 왼쪽 배경으로 메운다. 무늬 배경을 살린다."""
    top = max(lum(pal[px[y][x]]) for y in range(y0, y0 + h) for x in range(x0, x0 + w))
    hit = {(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w) if lum(pal[px[y][x]]) > top * 0.55}
    grow = {(x + dx, y + dy) for x, y in hit for dx in (-1, 0, 1, 2) for dy in (-1, 0, 1, 2)}
    for y in range(y0 - 1, y0 + h + 2):
        last = px[y][x0 - 2]
        for x in range(x0 - 1, x0 + w + 2):
            if (x, y) in grow:
                px[y][x] = last
            else:
                last = px[y][x]


def patch_gfx(rom, g12, font):
    idc = rom.filenames.idOf('data/rom/db/wbg0100_ch_lz.bin')
    ids = [rom.filenames.idOf(f'data/rom/db/wbg010{i}_sc_lz.bin') for i in (0, 1)]
    idp = rom.filenames.idOf('data/rom/db/wbg0100_pl_lz.bin')
    ch = lz10(bytes(rom.files[idc]))
    pal = struct.unpack_from('<256H', lz10(bytes(rom.files[idp])), 0x28)
    scs = [bytearray(lz10(bytes(rom.files[i]))) for i in ids]
    pages = [decode(ch[0x30:], struct.unpack_from('<1024H', s, 0x24)) for s in scs]
    for p, px in enumerate(pages):
        hist = {}
        for y in range(76, 168):
            for x in range(26, 160):
                hist[px[y][x]] = hist.get(px[y][x], 0) + 1
        bg = max(hist, key=hist.get)
        ink = max(hist, key=lambda v: lum(pal[v]))
        shadow = max((v for v in hist if v not in (bg, ink)), key=hist.get)
        for y in range(74, 170):
            for x in range(24, 236):
                px[y][x] = bg
        for i, c in enumerate(PAGE[p] + EXTRA[p]):
            bx, r, k = (24, i // 5, i % 5) if i < 30 else (104, (i - 30) // 5, (i - 30) % 5)
            x, y = bx + 16 * k, 72 + 16 * r
            if c in g12:
                glyph(px, g12[c], x + 2, y + 3, ink, shadow)
            elif c != ' ':
                for a, b in font.big(c):
                    dot(px, x + 8 + a + 1, y + b + 1, shadow)
                for a, b in font.big(c):
                    dot(px, x + 8 + a, y + b, ink)
        for r, w in enumerate(WORDS[p]):
            x = 176 + (56 - 12 * len(w)) // 2
            for j, c in enumerate(w):
                glyph(px, g12[c], x + j * 12, 72 + 16 * r + 3, ink, shadow)
        mask, tw = font.line('이름', True)
        label(px, 46, 26, 36, 13, mask, tw, pal)
        mask, tw = font.line('코멘트', True)
        label(px, 46, 50, 36, 13, mask, tw, pal)
        mask, tw = font.line('L:뒤로 R:앞으로', False)
        if tw > 72:
            raise SystemExit(f'자판 안내 폭 {tw}')
        label(px, 160, 29, 72, 9, mask, tw, pal, False)
    tiles, maps = encode(pages)
    if len(tiles) > 512:
        raise SystemExit(f'자판 타일 {len(tiles)} > 512')
    n = (len(tiles) + 31) // 32 * 32
    data = b''.join(tiles) + bytes(64) * (n - len(tiles))
    head = bytearray(ch[:0x30])
    struct.pack_into('<I', head, 8, 0x30 + len(data))
    struct.pack_into('<I', head, 0x14, 0x20 + len(data))
    struct.pack_into('<H', head, 0x18, n // 32)
    struct.pack_into('<I', head, 0x28, len(data))
    rom.files[idc] = compress(bytes(head) + data)
    for i, s, m in zip(ids, scs, maps):
        struct.pack_into('<1024H', s, 0x24, *m)
        rom.files[i] = compress(bytes(s))
    print('자판 타일', len(tiles))


def rebuild(rom, chn, scs, paint):
    """8bpp 그림 묶음을 픽셀로 풀어 고치고 다시 자른다. 타일 수는 원본 줄 수 안에서만."""
    idc = rom.filenames.idOf(f'data/rom/db/{chn}_ch_lz.bin')
    idp = rom.filenames.idOf(f'data/rom/db/{chn}_pl_lz.bin')
    ids = [rom.filenames.idOf(f'data/rom/db/{n}_sc_lz.bin') for n in scs]
    ch = lz10(bytes(rom.files[idc]))
    pal = struct.unpack_from('<256H', lz10(bytes(rom.files[idp])), 0x28)
    raw = [bytearray(lz10(bytes(rom.files[i]))) for i in ids]
    pages = [decode(ch[0x30:], struct.unpack_from('<1024H', s, 0x24)) for s in raw]
    paint(pages, pal)
    tiles, maps = encode(pages)
    old = (len(ch) - 0x30) // 64
    if len(tiles) > old:
        raise SystemExit(f'{chn} 타일 {len(tiles)} > {old}')
    data = b''.join(tiles) + bytes(64) * (old - len(tiles))
    rom.files[idc] = compress(ch[:0x30] + data)
    for i, s, m in zip(ids, raw, maps):
        struct.pack_into('<1024H', s, 0x24, *m)
        rom.files[i] = compress(bytes(s))
    print(chn, '타일', len(tiles), '/', old)


MENU = [(31, 33, 50, 14, '넷배틀'), (122, 25, 28, 14, '배틀'), (103, 41, 49, 14, '토너먼트'),
        (199, 33, 34, 14, '트레이드'), (31, 81, 50, 14, '팀배틀'), (122, 73, 28, 14, '팀'),
        (103, 89, 49, 14, '토너먼트'), (199, 81, 34, 14, '비교')]


def patch_net(rom, font):
    def text(px, pal, rows, dx=0, left=False, flat=False):
        for x, y, w, h, s in rows:
            mask, tw = font.line(s, True)
            if tw > w:
                raise SystemExit(f'통신 라벨 {s} 폭 {tw}')
            label(px, x + dx, y, w, h, mask, tw, pal, True, left, flat)

    rebuild(rom, 'wbg0200', ['wbg0200'], lambda pg, pal: text(pg[0], pal, MENU, flat=True))

    def rec(pg, pal):
        for px, dx in zip(pg, (0, 32)):
            text(px, pal, [(17, 132, 40, 14, '전적'), (38, 148, 12, 15, '전'), (70, 148, 11, 15, '승')], dx, True)
    rebuild(rom, 'wbg0300', ['wbg0300', 'wbg0301', 'wbg0302', 'wbg0303'], rec)
    rebuild(rom, 'wbg0500', ['wbg0500'], lambda pg, pal: text(pg[0], pal, [(72, 23, 66, 14, '엔트리 네임')]))

    def mini(pg, pal):
        px = pg[0]
        for rect in ((66, 33, 56, 14), (60, 64, 136, 18), (60, 96, 136, 18), (60, 128, 136, 18)):
            soft_erase(px, *rect, pal)
        mask, tw = font.line('룰 설명', False)
        for a_, b_ in mask:
            dot(px, 74 + a_, 36 + b_, white(pal))
        for i, t in enumerate(('나오는 내비들의 순서를', '잘 외워서', '그 순서대로 터치!!')):
            m, tw = font.line(t, True)
            ox = 128 - tw // 2
            for a_, b_ in m:
                dot(px, ox + a_ + 1, 66 + 32 * i + b_ + 1, black(pal))
            for a_, b_ in m:
                dot(px, ox + a_, 66 + 32 * i + b_, white(pal))
    rebuild(rom, 'MiniBg00', ['MiniBg00'], mini)
    rebuild(rom, 'bg0501', ['bg0501'], lambda pg, pal: text(pg[0], pal, [(38, 7, 44, 14, '프로그램'), (38, 92, 52, 14, '폴더')], flat=True))


SORTBOX = [(14, 13, 56, 13, '배낭 정렬', True), (24, 56, 44, 13, '가나다', False), (24, 70, 44, 13, '코드', False),
           (24, 86, 44, 13, '공격력', False), (24, 102, 44, 13, '속성', False), (24, 118, 44, 13, '장수', False),
           (24, 134, 44, 13, '칩 용량', False)]


def cell_paint(rom, font, pre, idx, rows, part=None):
    """OBJ 셀 하나를 캔버스로 풀어 글자를 그리고 제자리에 쓴다. rows: (x, y, w, h, 글자, 가운데)."""
    import ncer
    gid = rom.filenames.idOf(f'data/rom/dc/{pre}g_lz.bin')
    cid = rom.filenames.idOf(f'data/rom/dc/{pre}c_lz.bin')
    g = bytearray(lz10(bytes(rom.files[gid])))
    head = 0x30
    cell = ncer.cells(lz10(bytes(rom.files[cid])))[idx]
    if part is not None:
        cell = [cell[k] for k in (part if isinstance(part, (list, tuple)) else [part])]
    x0, y0 = min(p['x'] for p in cell), min(p['y'] for p in cell)
    W = max(p['x'] + p['w'] for p in cell) - x0
    H = max(p['y'] + p['h'] for p in cell) - y0
    px = [[0] * W for _ in range(H)]

    def walk():
        for p in cell:
            tw = p['w'] // 8
            for j in range(tw * p['h'] // 8):
                yield head + (p['tile'] + j) * 32, p['x'] - x0 + j % tw * 8, p['y'] - y0 + j // tw * 8
    for t, cx, cy in walk():
        for y in range(8):
            for x in range(8):
                px[cy + y][cx + x] = (g[t + y * 4 + x // 2] >> (4 * (x & 1))) & 15
    for x, y, w, h, s, center in rows:
        mask, tw = font.line(s, True)
        if tw > w:
            raise SystemExit(f'{pre}.{idx} {s} 폭 {tw}')
        hist = {}
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                hist[px[yy][xx]] = hist.get(px[yy][xx], 0) + 1
        bg = max(hist, key=hist.get)
        ink = max(hist)
        edge = min(v for v in hist if v)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                px[yy][xx] = bg
        ox = x + (w - tw) // 2 if center else x
        for a, b in mask:
            if b + 1 < h and ox + a + 1 < W:
                px[y + b + 1][ox + a + 1] = edge
        for a, b in mask:
            if b < h:
                px[y + b][ox + a] = ink
    for t, cx, cy in walk():
        for y in range(8):
            for x in range(0, 8, 2):
                g[t + y * 4 + x // 2] = px[cy + y][cx + x] | px[cy + y][cx + x + 1] << 4
    rom.files[gid] = compress(bytes(g))


def patch_cells(rom, font):
    cell_paint(rom, font, 'wo04', 28, SORTBOX)
    cell_paint(rom, font, 'wo03', 14, [(0, 0, 40, 16, '도감', True), (0, 16, 40, 16, '비교', True)])
    cell_paint(rom, font, 'wo03', 15, [(0, 0, 32, 16, '기록', True), (0, 16, 32, 16, '비교', True)])
    cell_paint(rom, font, 'wo02', 8, [(14, 0, 36, 16, '팀', True), (0, 16, 64, 16, '토너먼트', True)], part=0)
    cell_paint(rom, font, 'wo03', 8, [(0, 0, 40, 16, '부모기로', True), (0, 16, 40, 16, '설정', True)], part=[0, 1])
    cell_paint(rom, font, 'wo03', 9, [(0, 0, 48, 16, '목록', True), (0, 16, 48, 16, '갱신', True)], part=[0, 1])
    cell_paint(rom, font, 'wo03', 40, [(0, 0, 40, 16, '목록', True), (0, 16, 40, 16, '갱신', True)], part=[0, 1])
    for pre, a, b in (('wo02', 3, 4), ('wo03', 6, 7), ('wo05', 10, 11)):
        cell_paint(rom, font, pre, a, [(0, 0, 16, 16, '예', True)])
        cell_paint(rom, font, pre, b, [(0, 0, 32, 16, '아뇨', True)])
    cell_paint(rom, font, 'po05', 9, [(0, 0, 16, 16, '없음', True)])
    cell_paint(rom, font, 'wo08', 21, [(0, 0, 16, 16, '없음', True)])
    for pre, idx in (('po11', 29), ('po12', 14)):
        cell_paint(rom, font, pre, idx, [(0, 16, 38, 16, '공격', False), (0, 32, 38, 16, '칩', False)])
    print('통신 셀 라벨 완료')
