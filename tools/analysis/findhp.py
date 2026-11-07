"""전투 중 적 HP 주소 찾기: u16==40 후보 중 값이 나란히 HP/최대HP 로 있고, 내비 HP 값 근처가 아닌 곳을 쓰기 시험.
사용법: findhp.py 롬 상태 이름"""
import json
import os
import struct
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st, name = sys.argv[1:4]
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
b0 = 0x02200000
ram = bytes(m[b0:0x02380000])
cand = [b0 + o for o in range(0, len(ram) - 2, 2) if struct.unpack_from('<H', ram, o)[0] == 40]
print(len(cand))
log = [hex(a) for a in cand]
for a in cand:
    n = (a - b0)
    near = struct.unpack_from('<8H', ram, max(n - 8, 0))
    print(hex(a), near)
json.dump(log, open(f'work/{name}.json', 'w'))
emutest.shutdown()
