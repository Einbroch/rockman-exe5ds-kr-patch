"""후보 묶음을 값 7 로 쓰고 커스텀을 닫아 적 HP 표시가 바뀌는지 본다. hpgroup.py 롬 상태 이름 시작hex 끝hex"""
import json
import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st, name, lo, hi = sys.argv[1:6]
lo, hi = int(lo, 16), int(hi, 16)
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
L = [int(x, 16) for x in json.load(open('work/hp.json'))]
for a in L:
    if lo <= a < hi:
        m[a:a + 2:1] = bytes(2)
emu.run(30)
emu.shot(name + '0')
emu.press(emutest.KEYS['A'], after=30)
emu.press(emutest.KEYS['ST'], after=30)
emu.press(emutest.KEYS['A'], after=100)
for i in range(12):
    emu.run(120)
    emu.shot(f'{name}{i:02d}')
    if i > 2:
        emu.press(emutest.KEYS['A'], after=20)
emu.shots=[f'{name}{i:02d}' for i in range(12)]
emu.grid(name, cols=6)
emu.save(name + '_end')
emutest.shutdown()
