"""미션 번호를 넣은 뒤 HP 워프 순간 목적지를 미션 맵으로 바꾼다.
사용법: libwarp.py 롬 방상태 이름 영역(16진) 서브"""
import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from desmume.controls import keymask  # noqa: E402

rom, st, name, area, sub = sys.argv[1:6]
area, sub = int(area, 16), int(sub)
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
K = emutest.KEYS


def hold(keys, n):
    for k in keys:
        emu.e.input.keypad_add_key(keymask(K[k]))
    emu.run(n)
    for k in keys:
        emu.e.input.keypad_rm_key(keymask(K[k]))
    emu.run(10)


for k, n in (('U', 30), ('RI', 30), ('D', 30), ('LE', 30)):
    hold([k], n)
hold(['U', 'RI'], 40)
emu.press(K['R'], after=150)
for _ in range(10):
    emu.press(K['A'], after=110)
emu.press(K['R'], after=240)        # 시험 롬 plugout: 미션 번호 기록 후 방으로
emu.press(K['R'], after=150)
for _ in range(10):
    emu.press(K['A'], after=110)
print('미션 상태', bytes(m[0x02165CA8:0x02165CB0]).hex(), '맵', bytes(m[0x02160024:0x02160026]).hex(), flush=True)
hold(['U'], 150)
hold(['U'], 150)
hold(['RI'], 100)
hold(['RI'], 60)
emu.e.input.keypad_add_key(keymask(K['RI']))
hit = False
for f in range(900):
    emu.run(1)
    a = bytes(m[0x02160024:0x02160026])
    if a[0] != 0x88 and not hit:
        print('프레임', f, '변화', a.hex(), bytes(m[0x02168630:0x02168632]).hex(), flush=True)
        m[0x02160024:0x02160026:1] = bytes([area, sub])
        m[0x02168630:0x02168632:1] = bytes([area, sub])
        hit = True
        emu.e.input.keypad_rm_key(keymask(K['RI']))
    if hit and f % 120 == 0:
        emu.shot(f'{name}{len(emu.shots):02d}')
print('끝 맵', bytes(m[0x02160024:0x02160026]).hex(), '미션', bytes(m[0x02165CA8:0x02165CB0]).hex(), flush=True)
for i in range(10):
    emu.press(K['A'], after=110)
    emu.shot(f'{name}{len(emu.shots):02d}')
emu.save(name + '_end')
emu.grid(name, cols=7)
emutest.shutdown()
