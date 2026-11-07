#!/usr/bin/env python3
"""한글판 빌드. 사용법: python tools/build.py [--release] [출력.nds]
--release 는 미번역·미지 글자가 하나라도 있으면 멈춘다(개발 빌드는 미번역을 ? 로 표시)."""
import collections
import glob
import json
import pathlib
import re
import shutil
import struct
import sys

import ndspy.rom

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import engine  # noqa: E402
import exe1k_hangul  # noqa: E402
import kotext  # noqa: E402
import namekb  # noqa: E402
from kotext import HANGUL, JP  # noqa: E402
from lz import compress as lz_compress  # noqa: E402
from scan_msg import lz10  # noqa: E402

SRC_ROM = ROOT / '0099 - Rockman EXE 5 DS - Twin Leaders (J)(WRG).nds'
SRC_SHA = '0070ba09cf007cd61e40000c08a8b3aaedb6e6fd1e7fa6ae97a602fe2ee920ec'
BDF = ROOT.parent / 'Rockman exe 4.5' / 'external' / 'fonts' / 'Galmuri11.bdf'
EXE1K = ROOT.parent / 'Rockman exe 2' / 'Battle Network Rockman EXE 1 [K].gba'
NOISE = re.compile(r'_srn$|^a_icon|^a_shl|^a_pshl|^a_efc|^a_dat')
# ARM9 에 박힌 아카이브: 이름 → 주소
STATIC = {'a_alphabet': 0x2108524, 'a_chipinf0': 0x21288d8, 'a_chipinf1': 0x212b388, 'a_chipname0': 0x212c848,
          'a_chipname1': 0x212d1c8, 'a_emname0': 0x212d760, 'a_emname1': 0x212dff8, 'a_foldname': 0x20d7874,
          'a_iboxdata': 0x20ca77c, 'a_itemname': 0x20d78d0, 'a_pl_name': 0x20d7618, 'a_prgmname': 0x20d741c}


def bdf_glyphs():
    """Galmuri11 → {글자: 12×12 비트 격자}."""
    found = {}
    for block in BDF.read_text(encoding='utf-8').split('STARTCHAR ')[1:]:
        lines = block.splitlines()
        cp = int(next(x.split()[1] for x in lines if x.startswith('ENCODING ')))
        if cp < 0x20 or cp > 0xFFFF:
            continue
        w, h, xoff, yoff = map(int, next(x for x in lines if x.startswith('BBX ')).split()[1:])
        start = lines.index('BITMAP') + 1
        rows = [int(x, 16) for x in lines[start:start + h]]
        top = 11 - h - yoff
        if w + xoff > 12 or xoff < 0 or top < 0 or top + h > 12:
            continue
        grid = [[0] * 12 for _ in range(12)]
        stride = ((w + 7) // 8) * 8
        for y, row in enumerate(rows):
            for x in range(w):
                if row & (1 << (stride - 1 - x)):
                    grid[top + y][xoff + x] = 1
        found[chr(cp)] = grid
    return found


def pack12(grid):
    bits = [grid[y][x] for y in range(12) for x in range(12)]
    return bytes(sum(bits[i + k] << (7 - k) for k in range(8)) for i in range(0, 144, 8))


def cell12(grid):
    """폰트 칸(16×12 4bpp, 0x60)."""
    out = bytearray(0x60)
    for y in range(12):
        for x in range(12):
            if grid[y][x]:
                out[y * 8 + x // 2] |= 1 << (4 * (x & 1))
    return bytes(out)


def ink8(source, ch):
    px = exe1k_hangul.ink(source, ch)
    if px is None:   # KS X 1001 밖 음절은 대사에만 쓰인다: 메뉴 칸은 비운다
        print('8×16 글리프 없음(KS 밖):', ch)
        return set()
    return px


def pack16(px):
    return bytes(sum(0x80 >> x for x in range(8) if (x, y) in px) for y in range(1, 15))


def cell16(px, ink=1, shadow=2):
    grid = [[0] * 8 for _ in range(16)]
    for x, y in px:
        for dx, dy in ((1, 0), (0, 1), (1, 1)):
            if x + dx < 8 and y + dy < 16:
                grid[y + dy][x + dx] = shadow
    for x, y in px:
        grid[y][x] = ink
    return bytes(grid[y][x] | grid[y][x + 1] << 4 for y in range(16) for x in range(0, 8, 2))


# 라벨을 칸 수대로 이어 붙이는 화면: 원문과 같은 칸 수로 채운다
OVERRIDE = {'a_dm060d_LZ': {'そんなこと、おもうもんか!': '그런 생각 안 해!'},   # 슬롯 초과 방지
            'a_subsave_LZ': {'タイム': '타임 ', 'ライブラリ': '도감   ', 'チップ': '칩  ', 'クレジット': '크레딧  '}}
KANA_TABLE = re.compile(r'[ ぁ-ゖァ-ヺ゜ー~・"]{30,}')


def restore_kana(name, msg, old):
    """가나 입력표 스크립트는 원본 바이트로 되돌린다(길이가 같아야 한다)."""
    idx = {sc for sc, _, _, s in kotext.parse(kotext.tpl_text(name)) if KANA_TABLE.fullmatch(s.replace(chr(92), ''))}
    if not idx:
        return msg

    def table(b):
        n = struct.unpack_from('<H', b)[0] // 2
        return list(struct.unpack_from(f'<{n}H', b)) + [len(b)]
    ta, tb = table(msg), table(old)
    out = bytearray(msg)
    for i in idx:
        a0, a1, b0, b1 = ta[i], ta[i + 1], tb[i], tb[i + 1]
        if a1 - a0 != b1 - b0:
            raise SystemExit(f'{name} 스크립트 {i} 길이 다름 {a1 - a0} {b1 - b0}')
        out[a0:a1] = old[b0:b1]
    return bytes(out)


def translated_tpls(release):
    tm, skip = kotext.load_tm()
    pop = kotext.population()
    out, stats = {}, collections.Counter()
    missing = collections.Counter()

    def fn(s):
        if not JP.search(s):
            return None
        if s in tm:
            stats['번역'] += 1
            return tm[s]
        if s in skip:
            stats['제외'] += 1
            return None
        if KANA_TABLE.fullmatch(s.replace(chr(92), '')):
            # 전용 폰트(collabofont.pix)를 쓰는 가나 입력표: 자리 표시 뒤 원본 바이트로 복원
            stats['입력표'] += 1
            return JP.sub('?', s)
        stats['미번역'] += 1
        missing[s] += 1
        return JP.sub('?', s)

    for n in pop:
        if NOISE.search(n) or not pop[n]['rt']:
            continue
        t = kotext.tpl_text(n)
        if not any(JP.search(s) for s in kotext.strings(t)):
            continue
        over = OVERRIDE.get(n, {})
        new, c = kotext.substitute(t, lambda x: over[x] if x in over else fn(x))
        out[n] = new
    if release and missing:
        raise SystemExit(f'미번역 {len(missing)}개')
    return out, stats, missing


def main():
    release = '--release' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out_path = pathlib.Path(args[0]) if args else ROOT / 'build' / 'exe5ds_ko.nds'
    out_path.parent.mkdir(exist_ok=True)
    raw = SRC_ROM.read_bytes()
    import hashlib
    if hashlib.sha256(raw).hexdigest() != SRC_SHA:
        raise SystemExit('원본 롬 해시 불일치')
    tpls, stats, missing = translated_tpls(release)
    print('치환', dict(stats), '아카이브', len(tpls))
    (ROOT / 'work/missing.json').write_text(json.dumps(missing, ensure_ascii=False, indent=0), encoding='utf8')

    # 글자 빈도
    freq = collections.Counter()
    other = collections.Counter()
    for t in tpls.values():
        for s in kotext.strings(t):
            for c in s:
                if HANGUL.match(c):
                    freq[c] += 1
                elif ord(c) > 0x7F:
                    other[c] += 1
    table = kotext.assign(freq, namekb.KEEP + '칸앞')   # 자판 글자 + 내장 칩 설명 크기 유지
    kotext.write_tbl(table)
    print('음절', len(freq), '1바이트', sum(1 for v in table.values() if len(v) == 1))

    # 재인코딩
    src, dst = ROOT / 'work/ko_tpl', ROOT / 'work/ko_msg'
    for d in (src, dst):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    for n, t in tpls.items():
        (src / f'{n}.tpl').write_text(t, encoding='utf8', newline=chr(10))
    r = kotext.textpet('exe5dsko', src, 'tpl', dst, 'bin')
    if 'Done.' not in (r.stdout or ''):
        print((r.stdout or '')[-1500:], (r.stderr or '')[-500:])
        raise SystemExit('TextPet 실패')
    miss = [n for n in tpls if not (dst / f'{n}.msg').exists()]
    if miss:
        raise SystemExit(f'인코딩 실패 {len(miss)}: {miss[:8]}')

    rom = ndspy.rom.NintendoDSRom(raw)
    a9 = engine.Arm9(bytes(rom.arm9))
    pop = kotext.population()
    grew = []
    total_old = total_new = 0
    for n in tpls:
        msg = (dst / f'{n}.msg').read_bytes()
        old = (ROOT / 'work/msg' / f'{n}.msg').read_bytes()
        msg = restore_kana(n, msg, old)
        if n == 'a_collabo':
            msg = namekb.patch_tables(msg, table)
        total_old += len(old)
        total_new += len(msg)
        if len(msg) > len(old):
            grew.append((len(msg) - len(old), n, len(old), len(msg)))
        v = pop[n]
        fid = rom.filenames.idOf(v['path'])
        if v['kind'] == 'raw':
            rom.files[fid] = msg
        else:
            orig = bytes(rom.files[fid])
            head = lz10(orig)[:4]
            if struct.unpack('<I', head)[0] >> 8 != len(old) + 4 and struct.unpack('<I', head)[0] >> 8 != len(old):
                print('머리 다름', n, head.hex(), len(old))
            newhead = struct.pack('<I', (struct.unpack('<I', head)[0] & 0xFF) | ((len(msg) + (struct.unpack('<I', head)[0] >> 8) - len(old)) << 8))
            rom.files[fid] = lz_compress(newhead + msg)
        if n in STATIC:
            if len(msg) > len(old):
                raise SystemExit(f'ARM9 내장 아카이브가 원본보다 큼: {n} {len(old)} -> {len(msg)}')
            else:
                a9.put(STATIC[n], msg + bytes(len(old) - len(msg)), n, old)
    print('원본', total_old, '번역', total_new, f'{total_new / total_old:.3f}')
    grew.sort(reverse=True)
    print('커진 곳', len(grew), grew[:12])
    (ROOT / 'work/grew.json').write_text(json.dumps(grew, ensure_ascii=False), encoding='utf8')

    # 글리프
    g12 = bdf_glyphs()
    source = exe1k_hangul.load(EXE1K)
    p12, p16 = bytearray(), bytearray()
    two = sorted((c for c, v in table.items() if len(v) == 2), key=lambda c: kotext.glyph_index(table[c]))
    for c in two:
        p12 += pack12(g12[c])
        p16 += pack16(ink8(source, c))
    single = []
    for c, v in table.items():
        if len(v) == 1:
            i = v[0]
            single.append(i)
            px = ink8(source, c)
            a9.put(engine.F12 + i * 0x60, cell12(g12[c]), f'12 {c}')
            a9.put(engine.F8 + i * 0x40, cell16(px), f'8 {c}')
            a9.put(engine.FS + i * 0x40, cell16(px, 2, 1), f's {c}')
    info = engine.install(a9, bytes(p12), bytes(p16), single)
    print('엔진', info)
    rom.arm9 = bytes(a9.d)
    # 그림 글자
    import gfx_cells
    gfx_cells.patch_all(rom)
    gfx_cells.patch_lib(rom, gfx_cells.Font())
    gfx_cells.patch_mapname(rom)
    namekb.patch_gfx(rom, g12, gfx_cells.Font())
    namekb.patch_overlay(rom, table)
    namekb.patch_net(rom, gfx_cells.Font())
    namekb.patch_cells(rom, gfx_cells.Font())
    import gfx_bg
    gfx_bg.patch_all(rom, gfx_cells.Font())
    gfx_bg.patch_stop(rom, gfx_cells.Font())
    gfx_bg.patch_result(rom, gfx_cells.Font())
    gfx_bg.patch_movemap(rom, gfx_cells.Font())
    import gfx_logo
    gfx_logo.patch(rom)
    data = rom.save()
    out_path.write_bytes(data)
    print(out_path, len(data), 'crc', hex(__import__('zlib').crc32(data)))
    print('기타 글자', other.most_common(40))


if __name__ == '__main__':
    main()
