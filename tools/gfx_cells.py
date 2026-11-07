#!/usr/bin/env python3
"""dc/po??·wo?? 셀의 구운 라벨 한글화(NCER 셀표로 타일 위치를 찾는다).
SPEC: {묶음: {셀 또는 (셀, 줄y): 글자}}. 색은 칸에서 읽는다(바깥과 맞닿는 비율이 큰 색 = 외곽).
칸보다 넓으면, 또는 한 타일을 두 라벨이 다르게 쓰면 빌드를 멈춘다."""
import collections
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import exe1k_hangul  # noqa: E402
import ncer  # noqa: E402
from lz import compress  # noqa: E402
from scan_msg import lz10  # noqa: E402

BDF7 = ROOT.parent / '폰트' / 'Galmuri-v2.24.29' / 'Galmuri7.bdf'
SPEC = {
    'po01': {0: '칩 폴더', 1: '서브칩', 2: '라이브러리', 3: '넷내비', 4: 'E메일', 5: '키 아이템', 6: '통신', 7: '맵', 8: '세이브'},
    'po02': {18: '장비', 19: '편집', 20: '폴더1', 21: '폴더2', 22: '덤|폴더', 23: '견습|폴더', 24: '명인|폴더', 25: '악인|폴더',
             28: '대전|폴더', 29: '에그제5|폴더'},
    'po03': {34: '폴더 정렬', 35: '배낭 정렬', 36: '스탠더드', 37: '메가클래스', 38: '기가클래스', 39: '다크'},
    'po04': {0: '록맨', 1: '블루스', 2: '자이로맨', 3: '마그넷맨', 4: '서치맨', 5: '미니 에너지', 6: '풀 에너지', 7: '시노비대시',
             8: '언트랩', 9: '에너미 서치', 10: '오픈 록', 11: '나팜맨', 12: '메디', 13: '커널', 14: '섀도맨', 15: '넘버맨',
             16: '나이트맨', 17: '토마호크맨', 21: '토드맨', 28: '시노비대시', 29: '언트랩', 30: '에너미 서치',
             39: 'FC록맨', 40: 'SC록맨'},
    'po05': {21: '다음', (17, 3): '프로그램', (18, 2): '버스터', (19, 3): '소울', (20, 4): '내비커스 기동'},
    'po06': {10: '이전'},
    'po07': {(10, 56): '데이터를 세이브 중입니다', (10, 72): '전원을 끄지 마세요', (15, -29): '예', (16, -29): '아니요'},
    'po08': {(0, -38): '기타', (0, (0, 0)): '팀', (0, (0, 1)): '친구', (10, (0, 0)): '친구', (10, (0, 1)): '기타'},
    'po10': {1: '스탠더드', 2: '메가클래스', 3: '기가클래스', 4: '다크 칩', 5: '시크릿', 7: '이전', 8: '다음', 17: 'P.A메모',
             (6, -72): '패턴'},
    'po11': {14: '다운로드'},
    'po12': {9: '이전', 10: '다음', 15: '와이드소드', 16: '에어자이로', 17: '마그넷 배리어', 18: '나팜 발칸', 19: '서치스나이프',
             20: '힐링 펄스', 21: '커널 캐논', 22: '나이트 가드', 23: '연막탄', 24: 'T스윙', 25: '주사위플러스', 26: '기운리커버리'},
    'po13': {(11, -21): '아니요'},
    'po14': {1: '내비 프로그램', (0, -32): '맵 데이터', (0, (0, 0)): '중요한 것', (0, (0, 1)): 'P코드/배너'},
    'po15': {44: '칩 트레이드', (50, 78): '트레이드 시작'},
    'po17': {(15, -29): '예', (16, -29): '아니요'},
    'wo02': {10: '팀', (7, -16): '팀배틀', (9, -64): '트레이드'},
    'wo03': {10: '싱글|배틀', 11: '트리플|배틀', 12: '연습', 13: '실전', 16: '배틀칩', 17: '프로그램'},
    'wo04': {11: '배낭 정렬', 12: '트레이드 OK!'},
    'wo08': {24: '선택 중', 110: '세이브중', 111: '세이브중.', 112: '세이브중.', 113: '세이브중..'},
}


def load_bdf7():
    out = {}
    for block in BDF7.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        lines = block.splitlines()
        cp = int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        w, h, xo, yo = map(int, next(x for x in lines if x.startswith('BBX ')).split()[1:])
        dw = int(next(x for x in lines if x.startswith('DWIDTH ')).split()[1])
        s = lines.index('BITMAP') + 1
        rows = [int(x, 16) for x in lines[s:s + h]]
        stride = ((w + 7) // 8) * 8
        top = 7 - h - yo
        out[chr(cp)] = (dw, {(xo + x, top + y) for y, r in enumerate(rows) for x in range(w) if r & (1 << (stride - 1 - x))})
    return out


class Font:
    def __init__(self):
        import build
        self.build = build
        self.src = exe1k_hangul.load(build.EXE1K)
        self.a9 = (ROOT / 'work/jp/arm9.bin').read_bytes()
        self.small = load_bdf7()
        tb = {}
        for ln in (ROOT / 'external/textpet-plugins/exe5ds-utf8.tbl').read_text(encoding='utf8').splitlines():
            if '=' in ln:
                k, v = ln.split('=', 1)
                tb.setdefault(v, k)
        self.tb = tb

    def big(self, c):
        if '가' <= c <= '힣':
            return self.build.ink8(self.src, c)
        k = self.tb[c]
        i = int(k, 16) if len(k) == 2 else 0xE4 + int(k[2:], 16)
        cell = self.a9[0x119784 + i * 0x40:0x119784 + (i + 1) * 0x40]
        return {(x, y) for y in range(16) for x in range(8) if (cell[y * 4 + x // 2] >> (4 * (x & 1))) & 15 == 1}

    def line(self, s, tall):
        px, x = set(), 0
        if s.startswith('#'):          # 큰 글자(16px): 고딕을 줄여서
            from PIL import Image, ImageDraw, ImageFont
            f = ImageFont.truetype(str(ROOT.parent / '폰트' / 'S-Core_Dream_OTF' / 'SCDream7.otf'), 80)
            l, t, r, b = f.getbbox(s[1:])
            im = Image.new('L', (r + 20, b + 20), 0)
            ImageDraw.Draw(im).text((10, 10), s[1:], font=f, fill=255)
            im = im.crop(im.getbbox()).resize((58, 15), Image.LANCZOS)
            return {(a, b_) for b_ in range(15) for a in range(58) if im.getpixel((a, b_)) > 120}, 58
        for c in s:
            if tall:
                if c == ' ':
                    x += 4
                    continue
                px |= {(x + a, b) for a, b in self.big(c)}
                x += 8
            else:
                adv, ink = self.small[c]
                px |= {(x + a, b) for a, b in ink}
                x += adv
        return px, x


def parts_of(cell, row):
    if isinstance(row, tuple):         # (조각 번호, 줄 번호): 큰 OBJ 안의 16px 줄 하나
        p = dict(cell[row[0]])
        k = row[1]
        tw = p['w'] // 8
        p.update(y=p['y'] + k * 16, h=16, tile=p['tile'] + k * 2 * tw)
        return [p]
    return sorted([p for p in cell if row is None or p['y'] == row], key=lambda p: (p['y'], p['x']))


def apply(x, ps, text, font, owner, name, base=0x30, yshift=0, colors=None):
    """x = 해제본(bytearray). 라벨 하나를 그린다."""
    x0 = min(p['x'] for p in ps)
    y0 = min(p['y'] for p in ps)
    W = max(p['x'] + p['w'] for p in ps) - x0
    H = max(p['y'] + p['h'] for p in ps) - y0
    tiles = {}
    for p in ps:
        tw = p['w'] // 8
        for ty in range(p['h'] // 8):
            for tx in range(tw):
                t = base + (p['tile'] + ty * tw + tx) * 32
                if t + 32 > len(x):
                    raise SystemExit(f'{name}: 타일 범위 밖 {text}')
                tiles[(p['x'] - x0 + tx * 8, p['y'] - y0 + ty * 8)] = t
    pix = {}
    for (bx, by), t in tiles.items():
        for py in range(8):
            for px in range(8):
                pix[(bx + px, by + py)] = (x[t + py * 4 + px // 2] >> (4 * (px & 1))) & 15
    cnt = collections.Counter(v for v in pix.values() if v)
    if not cnt:
        raise SystemExit(f'{name}: 빈 칸 {text}')
    common, n = cnt.most_common(1)[0]
    bg = common if sum(cnt.values()) > 0.75 * len(pix) and n > 0.4 * len(pix) else 0
    ratio = {}
    for c in cnt:
        if c == bg:
            continue
        out = tot = 0
        for (a, b), v in pix.items():
            if v != c:
                continue
            tot += 1
            if any(pix.get((a + dx, b + dy), 0) in (0, bg) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out += 1
        ratio[c] = out / tot
    if not ratio:
        raise SystemExit(f'{name}: 색 판별 실패 {text}')
    edge = max(ratio, key=ratio.get)
    ink = min(ratio, key=ratio.get)
    if colors:
        ink, edge, bg = colors
    tall = H >= 14
    right = text.startswith('>')       # 뒷부분 타일을 공유하는 라벨은 오른쪽 정렬
    left = text.startswith('<')
    text = text.lstrip('><')
    if '|' in text:                    # 앞|뒤: 뒤쪽 32px 타일 공유. 뒤를 그 시작에 고정, 앞은 거기에 붙인다
        left, rt = text.split('|')
        ml, wl = font.line(left, tall)
        mr, wr = font.line(rt, tall)
        cut = W - 32
        if wl > cut:
            raise SystemExit(f'{name}: {text} 앞 폭 {wl} > {cut}')
        mask = {(a + cut - wl, b) for a, b in ml} | {(a + cut, b) for a, b in mr}
        tw, right = W, True
    else:
        mask, tw = font.line(text, tall)
    if tw > W + 1:
        raise SystemExit(f'{name}: {text} 폭 {tw} > {W}')
    ox = 0 if left else max(W - tw, 0) if right else max((W - tw) // 2, 0)
    oy = yshift if tall else max((H - 7) // 2, 0)
    new = {k: (v if (bg and v == 0) else bg) for k, v in pix.items()}
    if text == ' ':
        mask = set()
    for a, b in mask:
        k = (a + ox, b + oy)
        if k in new:
            new[k] = ink
    if edge != ink:
        for a, b in mask:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    k = (a + ox + dx, b + oy + dy)
                    if k in new and new[k] in (0, bg) and not (bg == 0 and pix.get(k) is None):
                        new[k] = edge
    for (bx, by), t in tiles.items():
        data = bytearray(32)
        for py in range(8):
            for px in range(0, 8, 2):
                data[py * 4 + px // 2] = new[(bx + px, by + py)] | new[(bx + px + 1, by + py)] << 4
        if t in owner and owner[t][1] != bytes(data):
            raise SystemExit(f'{name}: 타일 공유 충돌 {text} / {owner[t][0]}')
        owner[t] = (text, bytes(data))
        x[t:t + 32] = data
    return (W, tw, ink, edge, bg)


# 무압축 타일 파일: (타일, [(폭,높이)...], 글자)
RAW = {'data/rom/a/t_moji.bin': [
    (24, [(32, 16), (32, 16), (16, 16)], '처음부터'),
    (44, [(32, 16), (32, 16), (16, 16)], '이어하기'),
    (160, [(32, 16)], '블루스'),
    (140, [(32, 16)], '커널'),
    (260, [(32, 16), (32, 16), (32, 16)], '세이브 데이터 없음'),
    (180, [(32, 16), (16, 16)], '데이터 삭제'),
    (346, [(32, 16)], '이전'),
    (200, [(32, 16), (16, 16)], '컨버트'),
    (306, [(32, 16)], '예'),
    (326, [(32, 16)], '아니요'),
],
    # 폴더 편집 위 화면 제목. 숫자 칸(45, 47)은 그대로
    'data/rom/b/icon40_lz.bin': [
    (37, [(32, 16)], '>폴더', 2),
    (49, [(32, 16)], '배낭', 2),
]}
RAW_BASE = {'data/rom/b/icon40_lz.bin': 4}
ERR = []
# 리버레이트 카메라 안내: (부품들 [(타일, 폭)], 글자). 머리 0x20. 타일 공유에 맞춰 나눴다
COCKPIT = [([(2, 16)], '카메'), ([(16, 32)], '<라 이동'), ([(14, 16), (10, 32)], '<라 고속'),
           ([(7, 16)], '이전'), ([(4, 8)], ' '), ([(9, 8)], ' '), ([(24, 32)], '페이즈'), ([(28, 32)], '>목표 ')]
# 리버레이트 안내 띠: (프레임, 고칠 타일들, 글자). 143 은 공유 「!」
TELOP = [(2, (49, 57), '#성공'), (3, (69, 77), '#실패'), (6, (135, 139), '1페이즈 무적'), (7, (144, 148), 'HP 회복!'),
         (8, (150, 154), '오더포인트 GET'), (9, (158, 164, 162), '배틀칩 GET'), (10, (166, 170, 174), '적 1체에 큰 대미지!')]


def patch_lib(rom, font):
    import telop
    fid = rom.filenames.idOf('data/rom/a/libe_cockpit00.bin')
    x = bytearray(rom.files[fid])
    owner = {}
    for parts, text in COCKPIT:
        ps, px = [], 0
        for t, w in parts:
            ps.append(dict(x=px, y=0, w=w, h=8, tile=t, pal=0))
            px += w
        apply(x, ps, text, font, owner, 'cockpit', base=0x20)
    rom.files[fid] = bytes(x)
    fid = rom.filenames.idOf('data/rom/a/libe_telop00_bin_lz.bin')
    x = bytearray(lz10(bytes(rom.files[fid])))
    fr = telop.frames(bytes(x[4:]))
    owner = {}
    for k, ts, text in TELOP:
        ps = [dict(x=i['x'], y=i['y'], w=i['w'], h=i['h'], tile=i['t'], pal=0) for i in fr[k] if i['t'] in ts]
        if len(ps) != len(ts):
            raise SystemExit(f'안내 {k} 조각 수')
        cols = (13, 3, 0) if text.startswith('#') else (13, 13, 3)   # 큰 글자: 외곽 3 / 띠: 바탕 3
        apply(x, ps, text, font, owner, f'telop{k}', base=4 + 0x20, colors=cols)
    rom.files[fid] = compress(bytes(x))
    print('리버레이트 그림', len(COCKPIT) + len(TELOP))


def patch_all(rom, verbose=False):
    font = Font()
    grew = 0
    for pack, spec in SPEC.items():
        gid = rom.filenames.idOf(f'data/rom/dc/{pack}g_lz.bin')
        cid = rom.filenames.idOf(f'data/rom/dc/{pack}c_lz.bin')
        raw = bytes(rom.files[gid])
        x = bytearray(lz10(raw))
        cells = ncer.cells(lz10(bytes(rom.files[cid])) or bytes(rom.files[cid]))
        owner = {}
        for key, text in spec.items():
            c, row = key if isinstance(key, tuple) else (key, None)
            ps = parts_of(cells[c], row)
            if not ps:
                raise SystemExit(f'{pack}.{key}: 조각 없음')
            try:
                info = apply(x, ps, text, font, owner, f'{pack}.{key}')
            except SystemExit as e:
                ERR.append(str(e))
                continue
            if verbose:
                print(pack, key, text, info)
        new = compress(bytes(x))
        grew += len(new) - len(raw)
        rom.files[gid] = new
    # 네트 화면 「マップ」 단추: po00 셀 72 의 바탕과 한 조각(32×32 + 16×32)
    fid = rom.filenames.idOf('data/rom/dc/po00g_lz.bin')
    x = bytearray(lz10(bytes(rom.files[fid])))

    def pix(a, b):
        t, w = (748, 4) if a < 32 else (764, 2)
        o = 0x30 + (t + (b // 8) * w + (a % 32) // 8) * 32 + (b % 8) * 4 + (a % 8) // 2
        return o, 4 * (a % 8 & 1)
    get = lambda a, b: (x[pix(a, b)[0]] >> pix(a, b)[1]) & 15
    X0, X1, Y0, Y1 = 17, 42, 5, 19
    ink = get(20, 8)
    for b in range(Y0, Y1):
        cnt = collections.Counter(get(a, b) for a in range(X0, X1) if get(a, b) != ink)
        fill = cnt.most_common(1)[0][0] if cnt else get(X0, b)
        for a in range(X0, X1):
            o, sh = pix(a, b)
            x[o] = (x[o] & (0xF0 if sh == 0 else 0x0F)) | fill << sh
    mask, tw = font.line('맵', True)
    for a, b in mask:
        o, sh = pix(a + 25, b + 4)
        x[o] = (x[o] & (0xF0 if sh == 0 else 0x0F)) | ink << sh
    rom.files[fid] = compress(bytes(x))
    for path, rows in RAW.items():
        fid = rom.filenames.idOf(path)
        packed = path.endswith('_lz.bin')
        x = bytearray(lz10(bytes(rom.files[fid])) if packed else rom.files[fid])
        owner = {}
        for row_ in rows:
            tile, objs, text = row_[:3]
            ys = row_[3] if len(row_) > 3 else 0
            ps, px, t = [], 0, tile
            for w, h in objs:
                ps.append(dict(x=px, y=0, w=w, h=h, tile=t, pal=0))
                px += w
                t += w // 8 * (h // 8)
            try:
                apply(x, ps, text, font, owner, f'{path}:{tile}', base=RAW_BASE.get(path, 0), yshift=ys)
            except SystemExit as e:
                ERR.append(str(e))
        rom.files[fid] = compress(bytes(x)) if packed else bytes(x)
    if ERR:
        raise SystemExit(chr(10).join(ERR))
    print('그림 라벨', sum(len(v) for v in SPEC.values()), '압축 증가', grew)


MAPNAME = [(0x33, [(26, 0, 1), (28, 8, 4), (36, 40, 1)], '아키하라'),
           (0x1A, [(8, 0, 4)], '과학성'),
           (0x10, [(0, 0, 4)], '오란섬'),
           (0x24, [(16, 0, 4), (24, 32, 1)], '엔드 시티')]


def patch_mapname(rom):
    """a/mapname_obj_lz.bin: OBJ 표지판 네 개. 칸 표를 바꿔 긴 이름에 넓은 칸을 준다(타일 수 불변)."""
    from PIL import Image, ImageDraw, ImageFont
    fid = rom.filenames.idOf('data/rom/a/mapname_obj_lz.bin')
    x = bytearray(lz10(bytes(rom.files[fid])))
    P = 0x28
    T = x.find(struct.pack('<4I', 0x10, 0x1A, 0x24, 0x33))
    if T < 0:
        raise SystemExit('mapname_obj 칸 표를 못 찾았다')
    f = ImageFont.truetype(str(ROOT.parent / '폰트' / 'S-Core_Dream_OTF' / 'SCDream7.otf'), 80)
    for i, (off, parts, text) in enumerate(MAPNAME):
        struct.pack_into('<I', x, T + i * 4, off)
        W = sum(w * 8 for _, _, w in parts)
        l, t, r, b = f.getbbox(text)
        im = Image.new('L', (r + 20, b + 20), 0)
        ImageDraw.Draw(im).text((10, 10), text, font=f, fill=255)
        im = im.crop(im.getbbox()).resize((W - 2, 12), Image.LANCZOS)
        ink = {(a + 1, b_ + 2) for b_ in range(12) for a in range(W - 2) if im.getpixel((a, b_)) > 110}
        edge = {(a + dx, b_ + dy) for a, b_ in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - ink
        for t0, x0, w in parts:
            for j in range(w * 2):
                o = P + (t0 + j) * 32
                cx, cy = x0 + j % w * 8, j // w * 8
                for q in range(32):
                    v = 0
                    for k in (0, 1):
                        p = (cx + q % 4 * 2 + k, cy + q // 4)
                        v |= (1 if p in ink else 2 if p in edge else 0) << (4 * k)
                    x[o + q] = v
    rom.files[fid] = compress(bytes(x))
    print('지역 표지판 완료')
