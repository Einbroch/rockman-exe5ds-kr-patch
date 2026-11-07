#!/usr/bin/env python3
"""화면의 OBJ 를 OAM 그대로 다시 그려 어떤 타일이 어디 있는지 보여 준다.
사용법: oamdump.py 롬 상태 입력들 이름 → work/oam_<이름>.json, work/oam_<이름>.png"""
import json
import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from PIL import Image  # noqa: E402

rom, st, seq, name = sys.argv[1:5]
emu = emutest.Emu(rom, None if st == '-' else st)
if st == '-':
    emu.e.reset()
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
SIZES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64), (1, 0): (16, 8), (1, 1): (32, 8),
         (1, 2): (32, 16), (1, 3): (64, 32), (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
out = {}
for eng, oam, vram, pal, disp in (('A', 0x07000000, 0x06400000, 0x05000200, 0x04000000),
                                  ('B', 0x07000400, 0x06600000, 0x05000600, 0x04001000)):
    dc = int.from_bytes(bytes(m[disp:disp + 4]), 'little')
    shift = 5 + ((dc >> 20) & 3)
    o = bytes(m[oam:oam + 0x400])
    v = bytes(m[vram:vram + 0x40000])
    p = bytes(m[pal:pal + 0x200])
    rows = []
    im = Image.new('RGB', (512, 256), (40, 40, 40))
    for i in range(127, -1, -1):
        a0, a1, a2 = [int.from_bytes(o[i * 8 + k:i * 8 + k + 2], 'little') for k in (0, 2, 4)]
        if (a0 >> 8) & 3 == 2:
            continue
        y = a0 & 255
        x = a1 & 511
        sh, sz = a0 >> 14, a1 >> 14
        if sh == 3:
            continue
        w, h = SIZES[(sh, sz)]
        tile = a2 & 1023
        bank = a2 >> 12
        depth8 = bool(a0 & 0x2000)
        rows.append(dict(i=i, x=x, y=y, w=w, h=h, tile=tile, off=tile << shift, pal=bank, d8=depth8, hf=(a1 >> 12) & 1, vf=(a1 >> 13) & 1))
        if depth8:
            continue
        base = tile << shift
        for ty in range(h // 8):
            for tx in range(w // 8):
                t = base + (ty * (w // 8) + tx) * 32
                for py in range(8):
                    for px in range(8):
                        b = v[t + py * 4 + px // 2]
                        c = (b >> (4 * (px & 1))) & 15
                        if c:
                            q = int.from_bytes(p[bank * 32 + c * 2:bank * 32 + c * 2 + 2], 'little')
                            X = x + tx * 8 + px
                            Y = (y + ty * 8 + py) & 255
                            if X < 512:
                                im.putpixel((X, Y), ((q & 31) * 8, ((q >> 5) & 31) * 8, ((q >> 10) & 31) * 8))
    im.save(f'work/oam_{name}_{eng}.png')
    out[eng] = dict(dispcnt=dc, shift=shift, oam=rows)
    open(f'work/vram_obj{eng}_{name}.bin', 'wb').write(v)
json.dump(out, open(f'work/oam_{name}.json', 'w'), indent=0)
print('OBJ', {k: len(v['oam']) for k, v in out.items()}, {k: hex(v['dispcnt']) for k, v in out.items()})
emutest.shutdown()
