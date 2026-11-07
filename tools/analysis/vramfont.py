import os
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402

rom, st, seq = sys.argv[1:4]
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
    else:
        emu.press(emutest.KEYS[t], after=60)
m = emu.e.memory.unsigned
a9 = open('work/jp/arm9.bin', 'rb').read()
rd = lambda a, n: int.from_bytes(bytes(m[a:a + n]), 'little')
print('RES dispA', hex(rd(0x04000000, 4)), 'dispB', hex(rd(0x04001000, 4)))
for eng, io in (('A', 0x04000000), ('B', 0x04001000)):
    print('RES', eng, [hex(rd(io + 8 + b * 2, 2)) for b in range(4)])
print('RES bankctl', bytes(m[0x04000240:0x0400024A]).hex())
for name, base, size in (('bgA', 0x06000000, 0x80000), ('bgB', 0x06200000, 0x20000), ('objA', 0x06400000, 0x40000), ('objB', 0x06600000, 0x20000)):
    v = bytes(m[base:base + size])
    for fn, off in (('F8', 0x119784), ('FS', 0x120784)):
        g = a9[off + 0x28 * 0x40:off + 0x29 * 0x40]
        i = v.find(g)
        if i >= 0:
            start = i - 0x28 * 0x40
            print('RES', name, fn, '글리프0x28 at', hex(base + i), '폰트 시작', hex(base + start))
emutest.shutdown()
