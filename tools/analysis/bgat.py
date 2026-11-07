"""BG 레지스터로 화면 좌표의 타일을 읽어 파일에서 찾는다.
사용법: bgat.py 롬 상태 입력들 x y w h (픽셀, 아래 화면=엔진 판별은 dispcnt 스왑 없이 A 기준)"""
import collections
import os
import pathlib
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from scan_msg import lz10  # noqa: E402

rom, st, seq, X, Y, W, H = sys.argv[1:8]
X, Y, W, H = int(X, 0), int(Y, 0), int(W, 0), int(H, 0)
emu = emutest.Emu(rom, st)
for t in seq.split(','):
    if t.startswith('w'):
        emu.run(int(t[1:]))
    elif t[:1] == 'T':
        x, y = map(int, t[1:].split(':'))
        emu.e.input.touch_set_pos(x, y)
        emu.run(8)
        emu.e.input.touch_release()
        emu.run(40)
    elif t:
        emu.press(emutest.KEYS[t], after=50)
emu.run(40)
m = emu.e.memory.unsigned
rd = lambda a, n: int.from_bytes(bytes(m[a:a + n]), 'little')
disp = rd(0x04000000, 4)
print('dispcnt', hex(disp))
for eng, io, vb in (('A', 0x04000000, 0x06000000), ('B', 0x04001000, 0x06200000)):
    dc = rd(io, 4)
    for bg in range(4):
        if not dc & (1 << (8 + bg)):
            continue
        cnt = rd(io + 8 + bg * 2, 2)
        hs = rd(io + 0x10 + bg * 4, 2) & 511
        vs = rd(io + 0x12 + bg * 4, 2) & 511
        cb = ((cnt >> 2) & 15) * 0x4000
        sb = ((cnt >> 8) & 31) * 0x800
        if eng == 'A':
            cb += ((dc >> 24) & 7) * 0x10000
            sb += ((dc >> 27) & 7) * 0x10000
        d8 = (cnt >> 7) & 1
        size = cnt >> 14
        print(eng, 'BG', bg, 'cnt', hex(cnt), 'char', hex(cb), 'map', hex(sb), '8bpp', d8, 'size', size, 'scroll', hs, vs)
        tiles = []
        for ty in range(Y // 8, (Y + H + 7) // 8):
            for tx in range(X // 8, (X + W + 7) // 8):
                px, py = (tx * 8 + hs) & 511, (ty * 8 + vs) & 511
                sbk = 0
                if size in (1, 3) and px >= 256:
                    sbk += 1
                    px -= 256
                if size == 2 and py >= 256:
                    py -= 256
                    sbk += 1
                if size == 3 and py >= 256:
                    py -= 256
                    sbk += 2
                e = rd(vb + sb + sbk * 0x800 + (py // 8) * 64 + (px // 8) * 2, 2)
                tiles.append(e)
        tb = [e & 1023 for e in tiles]
        print('  tiles', [hex(t) for t in tb[:24]], 'pal', sorted({e >> 12 for e in tiles}))
        pieces = {}
        sz = 64 if d8 else 32
        for t in set(tb):
            b = bytes(m[vb + cb + t * sz:vb + cb + (t + 1) * sz])
            if len(set(b)) > 3:
                pieces[b] = t
        c = collections.Counter()
        for f in pathlib.Path('work/jp/fs').rglob('*'):
            if f.is_file():
                x = f.read_bytes()
                y = lz10(x) or x
                n = sum(p in y for p in pieces)
                if n:
                    c[f.name] = n
        print('  조각', len(pieces), c.most_common(4))
emutest.shutdown()
