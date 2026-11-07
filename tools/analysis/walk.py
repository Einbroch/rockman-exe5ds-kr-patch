"""오래 눌러 진행: A 연타 캡처. 사용법: walk.py 롬 상태|- 이름 횟수 대기"""
import sys,os
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
rom,st,name,n,w=sys.argv[1:6]
emu=emutest.Emu(rom,None if st=='-' else st)
if st=='-':
    emu.e.reset();emu.run(600)
    for _ in range(3):emu.press(emutest.Keys.KEY_START,after=120)
    emu.press(emutest.Keys.KEY_A,after=180)
for i in range(int(n)):
    emu.run(int(w))
    if i%int(sys.argv[6] if len(sys.argv)>6 else 1)==0: emu.shot(f'{name}{i:03d}')
    emu.press(emutest.Keys.KEY_A,after=8)
emu.save(f'{name}_end');emu.grid(name,cols=10,scale=0.5)
emutest.shutdown()
