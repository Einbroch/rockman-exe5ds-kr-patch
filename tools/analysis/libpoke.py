"""미션 상태 바이트를 찔러 보고 캡처. libpoke.py 롬 상태 미션번호+1 이름 입력"""
import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st, val, name, seq = sys.argv[1:6]
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
print('상태', bytes(m[0x02165CA8:0x02165CC0]).hex(), flush=True)
m[0x02165CAC:0x02165CAD:1] = bytes([int(val)])
for t in seq.split(','):
    if t.startswith('w'):
        emu.run(int(t[1:]))
    elif t == 'S':
        emu.shot(f'{name}{len(emu.shots):02d}')
    else:
        emu.press(emutest.KEYS[t], after=40)
print('상태', bytes(m[0x02165CA8:0x02165CC0]).hex(), flush=True)
emu.shot(f'{name}{len(emu.shots):02d}')
emu.save(name + '_end')
emu.grid(name, cols=6)
emutest.shutdown()
