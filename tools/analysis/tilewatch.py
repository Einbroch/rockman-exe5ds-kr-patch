import collections
import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st, seq = sys.argv[1:4]
emu = emutest.Emu(rom, st)
mem = emu.e.memory
reg = mem.register_arm9
c = collections.Counter()


def on(a, s):
    c[(hex(reg.r14), hex(reg.r4), hex(reg.r2))] += 1
    return 1


mem.register_exec(0x02012C84, on)
for t in seq.split(','):
    if t.startswith('w'):
        emu.run(int(t[1:]))
    elif t[0] == 'T':
        x, y = map(int, t[1:].split(':'))
        emu.e.input.touch_set_pos(x, y)
        emu.run(8)
        emu.e.input.touch_release()
        emu.run(40)
    elif t == 'S':
        emu.shot('tw')
    else:
        emu.press(emutest.KEYS[t], after=60)
print('RES', len(c), c.most_common(10))
emutest.shutdown()
