"""화면 처리기 강제 진입: forcescr.py 롬 상태 번호 이름 [입력들]
처리기 표 0x021030AC 의 번호(바이트 값=번호×4)를 상태 바이트에 써서 화면을 띄운다."""
import os, sys
sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest
rom, st, idx, name = sys.argv[1:5]
seq = sys.argv[5] if len(sys.argv) > 5 else ''
emu = emutest.Emu(rom, st)
mem = emu.e.memory
reg = mem.register_arm9
got = []
def on(a, sz):
    if not got:
        got.append(reg.r1)
    return 1
mem.register_exec(0x0205EC22, on)
emu.run(3)
a = got[0]
print('상태 주소 %x 값' % a, bytes(mem.unsigned[a:a + 8]).hex())
mem.unsigned[a] = int(idx, 0) * 4
mem.unsigned[a + 1] = 0
mem.unsigned[a + 2] = 0
mem.unsigned[a + 3] = 0
mem.register_exec(0x0205EC22, None)
emu.run(40)
emu.shot(name + '00')
emu.run(120)
emu.shot(name + '01')
print('후', bytes(mem.unsigned[a:a + 8]).hex())
for t in seq.split(','):
    if t.startswith('w'):
        emu.run(int(t[1:]))
    elif t == 'S':
        emu.shot('%s%02d' % (name, len(emu.shots)))
    elif t:
        emu.press(emutest.KEYS[t], after=50)
emu.shot('%s%02d' % (name, len(emu.shots)))
emu.grid(name, cols=4, scale=1)
emutest.shutdown()
