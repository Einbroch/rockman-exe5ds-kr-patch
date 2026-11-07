"""넷 상태에서 그 맵의 c/z/x 스크립트를 RAM 에서 callLiberationStart 로 바꾸고 돌아다니며 A.
사용법: libstart2.py 롬 상태 미션 이름 맵(st8a01) 입력들(쉼표, U40 등 + A)"""
import os
import pathlib
import re
import struct
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from desmume.controls import keymask  # noqa: E402
from play import HOLD, K  # noqa: E402

rom, st, mission, name, mapn, seq = sys.argv[1:7]
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
ram = bytes(m[0x02160000:0x021C7000])
done = 0
for f in pathlib.Path('work/ko_msg').glob(f'a_{mapn}_*.msg'):
    d = f.read_bytes()
    i = ram.find(d[:48])
    print(f.name, hex(0x02160000 + i) if i >= 0 else None, flush=True)
    if i < 0:
        continue
    a = 0x02160000 + i
    n = struct.unpack_from('<H', d)[0] // 2
    for o in set(struct.unpack_from('<%dH' % n, d)):
        if o + 5 <= len(d):
            m[a + o:a + o + 5:1] = bytes([0xFC, 0x03, 0x08, int(mission), 0xE6])
            done += 1
print('바꾼 스크립트', done, flush=True)
for t in seq.split(','):
    mm = re.fullmatch(r'(UL|UR|DL|DR|U|D|LE|RI)(\d+)', t)
    if mm:
        for k in HOLD[mm.group(1)]:
            emu.e.input.keypad_add_key(keymask(K[k]))
        emu.run(int(mm.group(2)))
        for k in HOLD[mm.group(1)]:
            emu.e.input.keypad_rm_key(keymask(K[k]))
        emu.run(10)
    elif t == 'S':
        emu.shot(f'{name}{len(emu.shots):02d}')
    elif t.startswith('w'):
        emu.run(int(t[1:]))
    else:
        emu.press(K[t], after=40)
emu.shot(f'{name}{len(emu.shots):02d}')
emu.save(name + '_end')
emu.grid(name, cols=7)
emutest.shutdown()
