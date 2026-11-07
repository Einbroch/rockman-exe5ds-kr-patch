#!/usr/bin/env python3
"""db/bg????_ch(NCGR 8bpp)·_sc(NSCR) 에 구운 라벨 한글화.
SPEC: (BG, x, y, w, h, 글자, 양식). 양식 'o' = 밝은 글자+어두운 외곽, 'd' = 어두운 글자(외곽 없음).
지울 때는 줄마다 네모 왼쪽 바깥 픽셀로 채운다. 네모의 타일이 네모 밖에서도 쓰이면 새 타일 없이는 안 되므로
그 칸을 보고하고 빌드를 멈춘다(빈 타일은 글자가 안 닿으면 건드리지 않는다)."""
import collections
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from lz import compress  # noqa: E402
from scan_msg import lz10  # noqa: E402

SPEC = [
    ('bg0100', 110, 176, 40, 14, '장비', 'o'),
    ('bg0100', 192, 176, 48, 14, '편집', 'o'),
    ('bg0301', 98, 2, 62, 14, '폴더 정렬', 'o'),
    ('bg0301', 98, 177, 62, 14, '배낭 정렬', 'o'),
    ('bg1501', 98, 177, 62, 14, '배낭 정렬', 'o'),
    ('bg1501', 186, 177, 60, 14, '칩 트레이드', 'o'),
    ('bg0600', 20, 9, 44, 14, '분류', 'd'),
    ('bg1300', 32, 18, 42, 14, '분류', 'd'),
    ('bg1700', 64, 155, 128, 14, '세이브 중입니다', 'o'),
    ('bg1700', 64, 171, 128, 14, '전원을 끄지 마세요', 'o'),
    ('bg0002', 199, 145, 28, 14, '맵', 'o'),
    ('bg1200', 33, 73, 42, 14, '공격', 'o'),
    ('bg1200', 33, 88, 42, 14, '칩', 'o'),
]
# 칩 정렬창(4bpp). 양식 뒤 'L' = 왼쪽 맞춤
_SORT = [(62, '가나다'), (78, '코드'), (94, '공격력'), (110, '속성'), (126, '장수'), (142, '칩 용량')]
for _n, _title in (('bg0302', '폴더 정렬'), ('bg1503', '배낭 정렬')):
    SPEC.append((_n, 100, 19, 60, 14, _title, 'o4'))
    for _y, _t in _SORT:
        SPEC.append((_n, 112, _y - 2, 48, 16, _t, 'oL4'))


def lum(c):
    return (c & 31) * 3 + ((c >> 5) & 31) * 6 + ((c >> 10) & 31)


def patch_all(rom, font):
    files = {}

    def load(n):
        if n not in files:
            ids = {k: rom.filenames.idOf(f'data/rom/db/{n}_{k}_lz.bin') for k in ('ch', 'sc', 'pl')}
            data = {k: bytearray(lz10(bytes(rom.files[i])) or bytes(rom.files[i])) for k, i in ids.items()}
            files[n] = (ids, data, {})
        return files[n]

    errs = []
    for n, x0, y0, w, h, text, style in SPEC:
        ids, data, wrote = load(n)
        ch, sc, pl = data['ch'], data['sc'], data['pl']
        pal = struct.unpack_from('<256H', pl, 0x28)
        four = '4' in style
        left = 'L' in style
        emap = list(struct.unpack_from('<1024H', sc, 0x24))
        where = {}
        for i, e in enumerate(emap):
            where.setdefault(e & 1023, []).append(i)

        def tile_of(px, py):
            return emap[py // 8 * 32 + px // 8]

        def get(px, py):
            e = tile_of(px, py)
            t, hf, vf = e & 1023, (e >> 10) & 1, (e >> 11) & 1
            ix, iy = px % 8, py % 8
            ix, iy = (7 - ix if hf else ix), (7 - iy if vf else iy)
            if four:
                return (ch[0x30 + t * 32 + iy * 4 + ix // 2] >> (4 * (ix & 1))) & 15
            return ch[0x30 + t * 64 + iy * 8 + ix]

        def put(px, py, v):
            e = tile_of(px, py)
            t, hf, vf = e & 1023, (e >> 10) & 1, (e >> 11) & 1
            ix, iy = px % 8, py % 8
            ix, iy = (7 - ix if hf else ix), (7 - iy if vf else iy)
            if four:
                o = 0x30 + t * 32 + iy * 4 + ix // 2
                ch[o] = (ch[o] & 0xF0) | v if ix % 2 == 0 else (ch[o] & 0x0F) | v << 4
                return
            ch[0x30 + t * 64 + iy * 8 + ix] = v

        rect = {(x, y): get(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
        used = {v for v in rect.values()}
        bank = (tile_of(x0, y0) >> 12) * 16 if four else 0
        ink = max(used, key=lambda c: lum(pal[bank + c]))
        edge = min(used, key=lambda c: lum(pal[bank + c]))
        if style == 'd':
            ink, edge = edge, None
        new = {}
        for y in range(y0, y0 + h):
            fill = get(x0 - 1, y)
            for x in range(x0, x0 + w):
                new[(x, y)] = fill
        mask, tw = font.line(text, True)
        if tw > w + 1:
            errs.append(f'{n} {text} 폭 {tw} > {w}')
            continue
        ox = x0 if left else x0 + (w - tw) // 2
        oy = y0 - 1
        for a, b in mask:
            if (a + ox, b + oy) in new:
                new[(a + ox, b + oy)] = ink
        if edge is not None:
            for a, b in mask:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        k = (a + ox + dx, b + oy + dy)
                        if k in new and new[k] != ink:
                            new[k] = edge
        # 라벨 칸의 타일을 다시 배정한다: 같은 내용은 합치고, 칸 안에서만 쓰이던 타일을 재사용
        cells = sorted({y // 8 * 32 + x // 8 for (x, y) in new})
        where = {}
        for i, e in enumerate(emap):
            where.setdefault(e & 1023, []).append(i)
        inside = set(cells)
        pool = sorted({emap[i] & 1023 for i in cells if all(j in inside for j in where[emap[i] & 1023])})
        content = {}
        for i in cells:
            cx, cy = (i % 32) * 8, (i // 32) * 8
            content[i] = tuple(new.get((cx + px, cy + py), get(cx + px, cy + py)) for py in range(8) for px in range(8))
        assign = {}
        for i in cells:
            c = content[i]
            if c not in assign:
                # 칸 밖과 공유하던 타일이 내용 그대로면 그대로 쓴다
                e = emap[i]
                same = not (e >> 10) & 3 and (e & 1023) not in pool and all(
                    get((i % 32) * 8 + px, (i // 32) * 8 + py) == c[py * 8 + px] for py in range(8) for px in range(8))
                if same:
                    assign[c] = e & 1023
                    continue
                if not pool:
                    errs.append(f'{n} {text}: 타일 부족')
                    break
                assign[c] = pool.pop(0)
        else:
            sz, st = (32, 4) if four else (64, 8)
            for c, t in assign.items():
                o = 0x30 + t * sz
                if four:
                    for k in range(32):
                        ch[o + k] = c[(k // 4) * 8 + (k % 4) * 2] | c[(k // 4) * 8 + (k % 4) * 2 + 1] << 4
                else:
                    ch[o:o + 64] = bytes(c)
            for i in cells:
                emap[i] = (emap[i] & 0xF000) | assign[content[i]]
            struct.pack_into('<1024H', sc, 0x24, *emap)
    if errs:
        raise SystemExit(chr(10).join(errs))
    grew = 0
    for n, (ids, data, _) in files.items():
        new = compress(bytes(data['ch']))
        grew += len(new) - len(rom.files[ids['ch']])
        rom.files[ids['ch']] = new
        rom.files[ids['sc']] = compress(bytes(data['sc']))
    print('BG 라벨', len(SPEC), '압축 증가', grew)


def patch_stop(rom, font):
    """a/stop.pix: 「アクセス中…」 띠(4bpp, 한 줄 16타일로 이어진 그림)."""
    fid = rom.filenames.idOf('data/rom/a/stop.pix')
    cid = rom.filenames.idOf('data/rom/a/stop.clt')
    x = bytearray(rom.files[fid])
    pal = struct.unpack_from('<16H', bytes(rom.files[cid]))

    def get(px, py):
        t = (py // 8) * 16 + px // 8
        q = x[t * 32 + (py % 8) * 4 + (px % 8) // 2]
        return (q >> (4 * (px % 8 & 1))) & 15

    def put(px, py, v):
        t = (py // 8) * 16 + px // 8
        o = t * 32 + (py % 8) * 4 + (px % 8) // 2
        x[o] = (x[o] & 0xF0) | v if px % 8 % 2 == 0 else (x[o] & 0x0F) | v << 4
    X0, X1, Y0, Y1 = 38, 90, 1, 15
    used = {get(a, b) for a in range(X0, X1) for b in range(Y0, Y1)}
    ink = max(used, key=lambda c: lum(pal[c]))
    edge = min(used, key=lambda c: lum(pal[c]))
    fill = {b: get(X0 - 1, b) for b in range(Y0, Y1)}
    mask, tw = font.line('접속중...', True)
    if tw > X1 - X0:
        raise SystemExit('stop 폭')
    ox, oy = X0 + (X1 - X0 - tw) // 2, Y0 - 1
    new = {(a, b): fill[b] for a in range(X0, X1) for b in range(Y0, Y1)}
    for a, b in mask:
        if (a + ox, b + oy) in new:
            new[(a + ox, b + oy)] = ink
    for a, b in mask:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                k = (a + ox + dx, b + oy + dy)
                if k in new and new[k] != ink:
                    new[k] = edge
    for (a, b), v in new.items():
        put(a, b, v)
    rom.files[fid] = bytes(x)


RESULT = [('result00.pix', 'result0.srn', 0, [(24, 48, 78, '버스팅 레벨'), (24, 32, 62, '딜리팅 타임')]),
          ('result01.pix', 'result1.srn', 1, [(24, 48, 78, '버스팅 레벨'), (24, 32, 62, '딜리팅 타임')]),
          ('result02.pix', 'result2.srn', 2, [(44, 40, 100, '칩 데이터 분실...')])]


TRADER = [(8, 2, 58, '트레이더', 'dark'), (206, 2, 36, '배낭', 'dark')]


def relabel(c, m, W, base, pal, rows, font, tag):
    """4bpp 타일 c(bytearray), 맵 m(list), 맵 값-base 가 타일. 칸 안에서 타일을 다시 배정해 글자를 그린다."""
    def get(x, y):
        e = m[y // 8 * W + x // 8]
        t = (e & 1023) - base
        if t < 0:
            return 0
        ix = 7 - x % 8 if e & 0x400 else x % 8
        iy = 7 - y % 8 if e & 0x800 else y % 8
        return (c[t * 32 + iy * 4 + ix // 2] >> (4 * (ix & 1))) & 15
    spare = []                         # 앞 줄에서 남은 타일은 뒤 줄이 쓴다
    for row in rows:
        x0, y0, w, text = row[:4]
        h = 14
        rect = {(x, y): get(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)}
        used = set(rect.values())
        ink = max(used, key=lambda v: lum(pal[v]))
        edge = min(used, key=lambda v: lum(pal[v]))
        new = {}
        for y in range(y0, y0 + h):
            fill = edge if len(row) > 4 else get(x0 - 1, y)
            for x in range(x0, x0 + w):
                new[(x, y)] = fill
        mask, tw = font.line(text, True)
        if tw > w + 1:
            raise SystemExit(f'{tag} {text} 폭 {tw}')
        ox, oy = x0, y0 - 1
        for a, b in mask:
            if (a + ox, b + oy) in new:
                new[(a + ox, b + oy)] = ink
        for a, b in mask:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (a + ox + dx, b + oy + dy)
                    if q in new and new[q] != ink:
                        new[q] = edge
        cells = sorted({y // 8 * W + x // 8 for (x, y) in new})
        inside = set(cells)
        where = {}
        for i, e in enumerate(m):
            where.setdefault(e & 1023, []).append(i)
        pool = sorted(set(spare) | {m[i] & 1023 for i in cells if (m[i] & 1023) >= base + 1 and all(j in inside for j in where[m[i] & 1023])})
        ntile = len(c) // 32
        pool += [t for t in range(base, base + ntile) if t not in where and not any(c[(t - base) * 32:(t - base + 1) * 32])] if W == 32 else []
        content = {}
        for i in cells:
            cx, cy = (i % W) * 8, (i // W) * 8
            content[i] = tuple(new.get((cx + a, cy + b), get(cx + a, cy + b)) for b in range(8) for a in range(8))
        assign = {}
        for i in cells:
            v = content[i]
            if v in assign:
                continue
            e = m[i]
            if not (e & 0xC00) and (e & 1023) >= base and (e & 1023) not in pool and \
                    all(get((i % W) * 8 + a, (i // W) * 8 + b) == v[b * 8 + a] for b in range(8) for a in range(8)):
                assign[v] = e & 1023
                continue
            if not pool:
                raise SystemExit(f'{tag} {text}: 타일 부족')
            assign[v] = pool.pop(0)
        for v, t in assign.items():
            o = (t - base) * 32
            for q in range(32):
                c[o + q] = v[(q // 4) * 8 + (q % 4) * 2] | v[(q // 4) * 8 + (q % 4) * 2 + 1] << 4
        for i in cells:
            m[i] = (m[i] & 0xF000) | assign[content[i]]
        spare = pool


def patch_result(rom, font):
    """a/result0?.pix(맵 값-1 이 타일, 24칸 폭), 칩 트레이더(b/c_trader_bg, 맵 최소값 기준)."""
    pal = struct.unpack('<48H', bytes(rom.files[rom.filenames.idOf('data/rom/a/resclt.bin')]))
    for pn, sn, k, rows in RESULT:
        pid, sid = rom.filenames.idOf('data/rom/a/' + pn), rom.filenames.idOf('data/rom/a/' + sn)
        c = bytearray(rom.files[pid])
        m = list(struct.unpack('<432H', bytes(rom.files[sid])))
        relabel(c, m, 24, 1, pal[k * 16:], rows, font, pn)
        rom.files[pid] = bytes(c)
        rom.files[sid] = struct.pack('<432H', *m)
    pid = rom.filenames.idOf('data/rom/b/c_trader_bg_lz.bin')
    sid = rom.filenames.idOf('data/rom/a/c_trader_bg_lz.srn')
    cid = rom.filenames.idOf('data/rom/b/c_trader_bg_lz.clt')
    c = bytearray(lz10(bytes(rom.files[pid]))[4:]) + bytes(32 * 12)   # 앞 4바이트 머리, 뒤에 빈 타일 12칸 추가
    raw = lz10(bytes(rom.files[sid]))
    head, raw = raw[:4], raw[4:]       # 앞 4바이트는 머리
    m = list(struct.unpack('<%dH' % (len(raw) // 2), raw))
    base = 1
    cl = lz10(bytes(rom.files[cid])) or bytes(rom.files[cid])
    pal = struct.unpack('<%dH' % (len(cl) // 2), cl) + (0,) * 16
    print('트레이더 맵', len(raw), hex(base), sorted({e >> 12 for e in m}))
    relabel(c, m, 32, base, pal, TRADER, font, 'trader')
    used = max(e & 1023 for e in m)
    c = c[:used * 32]
    rom.files[pid] = compress(struct.pack('<I', len(c) << 8) + bytes(c))
    rom.files[sid] = compress(head + struct.pack('<%dH' % len(m), *m))
    print('결과 창·트레이더 라벨 완료')


def patch_movemap(rom, font):
    """지도 화면 b_·k_movemap: 21행 1~10칸의 'L・Rボタン:せつめい'. 맵 값-2 가 타일, 판본별로 파일이 따로다."""
    for v in ('b/b_', 'k/k_'):
        pid = rom.filenames.idOf(f'data/rom/{v}movemap_pix_lz.bin')
        sid = rom.filenames.idOf(f'data/rom/{v}movemap00_srn_lz.bin')
        sid1 = rom.filenames.idOf(f'data/rom/{v}movemap01_srn_lz.bin')
        cid = rom.filenames.idOf(f'data/rom/{v}movemap.clt')
        c = bytearray(lz10(bytes(rom.files[pid])))
        raw = lz10(bytes(rom.files[sid]))[4:]
        raw1 = lz10(bytes(rom.files[sid1]))[4:]
        m = struct.unpack('<768H', raw)
        m1 = struct.unpack('<768H', raw1)
        cells = [e & 1023 for e in m[21 * 32 + 1:21 * 32 + 11]]
        cnt = collections.Counter(e & 1023 for e in m + m1)
        if any(cnt[t] != 1 for t in cells):
            raise SystemExit(f'{v}movemap 라벨 타일이 공유된다')
        cl = bytes(rom.files[cid])
        pal = struct.unpack('<%dH' % (len(cl) // 2), cl)
        k = m[21 * 32 + 1] >> 12
        vals = collections.Counter()
        for t in cells:
            for b in c[4 + (t - 2) * 32:4 + (t - 1) * 32]:
                vals[b & 15] += 1
                vals[b >> 4] += 1
        ink = max(vals, key=lambda q: lum(pal[k * 16 + q]))
        bg = vals.most_common(1)[0][0]
        mask, w = font.line('L·R 버튼: 설명', False)
        if w > 76:
            raise SystemExit(f'movemap 폭 {w}')
        for i, t in enumerate(cells):
            o = 4 + (t - 2) * 32
            for y in range(8):
                for x in range(8):
                    q = ink if (i * 8 + x - 4, y) in mask else bg
                    a = o + y * 4 + x // 2
                    c[a] = (c[a] & 0xF0) | q if x & 1 == 0 else (c[a] & 15) | q << 4
        rom.files[pid] = compress(bytes(c))
    print('지도 라벨 완료')
