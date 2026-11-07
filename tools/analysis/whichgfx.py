#!/usr/bin/env python3
"""지금 화면의 VRAM 타일이 어느 파일에서 왔는지 찾는다.
사용법: whichgfx.py 롬 상태 입력들 이름
결과: work/vram_<이름>.bin + 파일별 일치 타일 수(상위). 타일 32바이트 단위 해시 대조."""
import collections
import os
import pathlib
import re
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from desmume.controls import keymask  # noqa: E402
from scan_msg import lz10  # noqa: E402

rom, st, seq, name = sys.argv[1:5]
emu = emutest.Emu(rom, st)
for t in seq.split(','):
    if t.startswith('w'):
        emu.run(int(t[1:]))
    elif t[0] == 'T':
        x, y = map(int, t[1:].split(':'))
        emu.e.input.touch_set_pos(x, y)
        emu.run(8)
        emu.e.input.touch_release()
        emu.run(40)
    elif t:
        emu.press(emutest.KEYS[t], after=50)
emu.run(30)
emu.shot('wg_' + name)
mem = emu.e.memory.unsigned
reg = {'bgA': (0x06000000, 0x80000), 'bgB': (0x06200000, 0x20000), 'objA': (0x06400000, 0x40000), 'objB': (0x06600000, 0x20000)}
vram = {k: bytes(mem[a:a + n]) for k, (a, n) in reg.items()}
pathlib.Path(f'work/vram_{name}.bin').write_bytes(b''.join(vram.values()))
tiles = collections.defaultdict(set)
for k, v in vram.items():
    for o in range(0, len(v), 32):
        t = v[o:o + 32]
        if t.count(0) < 24 and len(set(t)) > 3:
            tiles[t].add((k, o))
print('타일', len(tiles))
hits = collections.Counter()
where = {}
for f in pathlib.Path('work/jp/fs').rglob('*'):
    if not f.is_file():
        continue
    d = f.read_bytes()
    x = lz10(d) or d
    n = 0
    regs = collections.Counter()
    for base in (0, 4, 8, 12, 16):
        for o in range(base, len(x) - 31, 32):
            t = x[o:o + 32]
            if t in tiles:
                n += 1
                for k, _ in list(tiles[t])[:1]:
                    regs[k] += 1
    if n:
        hits[f.name] = n
        where[f.name] = regs
for k, v in hits.most_common(200):
    if where[k].get('bgA'):
        print(k, v, dict(where[k]))
emutest.shutdown()
