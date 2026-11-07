"""아래 화면 BG 레이어 타일이 어느 db 파일인지 찾는다: whichbg.py 롬 상태"""
import os, sys, struct, pathlib
sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest
from scan_msg import lz10
emu = emutest.Emu(*sys.argv[1:3])
emu.run(5)
m = emu.e.memory.unsigned
base = 0x4000000
V = bytes(m[0x6000000:0x6020000])
disp = struct.unpack('<I', bytes(m[base:base + 4]))[0]
res = {}
for b in range(4):
    if not disp >> (8 + b) & 1:
        continue
    c = struct.unpack('<H', bytes(m[base + 8 + b * 2:base + 10 + b * 2]))[0]
    ch = (c >> 2 & 15) * 0x4000
    sc = (c >> 8 & 31) * 0x800
    b8 = c >> 7 & 1
    ts = set()
    for i in range(1024):
        e = struct.unpack_from('<H', V, sc + i * 2)[0]
        s = 64 if b8 else 32
        t = V[ch + (e & 1023) * s:ch + (e & 1023) * s + s]
        if len(set(t)) > 3:
            ts.add(t)
    print('BG', b, hex(c), 'tiles', len(ts), '8bpp' if b8 else '4bpp')
    hits = []
    for f in pathlib.Path('work/jp/fs/data/rom/db').glob('*_ch_lz.bin'):
        x = lz10(f.read_bytes())
        if not x:
            continue
        s = 64 if b8 else 32
        n = sum(1 for o in range(0x30, len(x) - s + 1, s) if x[o:o + s] in ts)
        if n:
            hits.append((n, f.name))
    print(sorted(hits)[-4:])
emutest.shutdown()
