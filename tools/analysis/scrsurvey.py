"""처리기 표 0x021030AC 의 화면을 하나씩 강제로 띄워 찍는다: scrsurvey.py 롬 상태 시작 끝"""
import os, sys
sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest
from PIL import Image
rom, st, a0, a1 = sys.argv[1:5]
emu = emutest.Emu(rom, st)
mem = emu.e.memory
A = 0x2168528
ims = []
for i in range(int(a0), int(a1)):
    emu.e.savestate.load_file(st)
    emu.run(3)
    mem.unsigned[A] = i * 4
    for k in (1, 2, 3):
        mem.unsigned[A + k] = 0
    emu.run(200)
    im = emu.e.screenshot().convert('RGB')
    im.save('work/emutest/ss%02d.png' % i)
    ims.append(im)
    print('scr', i, hex(mem.register_arm9.r15), flush=True)
W = 8
o = Image.new('RGB', (W * 174, ((len(ims) + W - 1) // W) * 262), 'white')
for n, im in enumerate(ims):
    o.paste(im.resize((170, 256)), (n % W * 174, n // W * 262))
o.save('work/ssgrid_%s.png' % a0)
emutest.shutdown()
