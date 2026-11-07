import os
import struct
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st = sys.argv[1:3]
emu = emutest.Emu(rom, st)
m = emu.e.memory.unsigned
ram = bytes(m[0x02160000:0x02200000])
cand = []
for o in range(0, len(ram) - 0x400, 2):
    if struct.unpack_from('<H', ram, o)[0] == 40:
        for step in (0xD8, 0xE0, 0x100, 0x120):
            if struct.unpack_from('<H', ram, o + step)[0] == 40:
                cand.append((0x02160000 + o, step))
print('후보', [(hex(a), hex(s)) for a, s in cand][:12])
for a, s in cand[:12]:
    for k in (0, 1):
        m[a + k * s:a + k * s + 2:1] = b'\x00\x00'
for i in range(10):
    emu.run(100)
    emu.shot(f'kl{i:02d}')
    emu.press(emutest.KEYS['A'], after=30)
emu.save('kl_end')
emu.grid('kl', cols=5)
emutest.shutdown()
