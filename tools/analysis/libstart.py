"""넷 상태에서 L 대화 스크립트(RAM 슬롯)를 callLiberationStart 로 바꿔 미션 시작.
사용법: libstart.py 롬 상태 미션 이름 [추가 입력]"""
import os
import struct
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from play import K  # noqa: E402

rom, st, mission, name = sys.argv[1:5]
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
SLOT = 0x0219FFB0
t = bytes(m[SLOT:SLOT + 2])
n = struct.unpack('<H', t)[0] // 2
print('표 ', n, bytes(m[SLOT:SLOT + 16]).hex(), flush=True)
offs = struct.unpack('<%dH' % n, bytes(m[SLOT:SLOT + n * 2]))
for o in set(offs):
    if o < 0x1800:
        m[SLOT + o:SLOT + o + 5:1] = bytes([0xFC, 0x03, 0x08, int(mission), 0xE6])
for k in sys.argv[5].split(','):
    emu.press(K[k], after=120)
    emu.shot(f'{name}k{k}')
for i in range(14):
    emu.run(120)
    emu.shot(f'{name}{i:02d}')
    if i >= 3:
        emu.press(K['A'], after=10)
emu.save(name + '_end')
emu.grid(name, cols=7)
emutest.shutdown()
