"""파일 열기 기록: 사용법 fileopen.py 롬 상태 입력들"""
import sys,os
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
rom,st,seq=sys.argv[1:4]
emu=emutest.Emu(rom,None if st=='-' else st)
if st=='-':emu.e.reset()
mem=emu.e.memory;reg=mem.register_arm9
log=[]
TBL=0x21516c4
def s(a):
    b=bytes(mem.unsigned[a:a+48]);return b.split(b'\0')[0].decode('ascii','replace')
def on(a,sz):
    p=int.from_bytes(bytes(mem.unsigned[TBL+reg.r0*4:TBL+reg.r0*4+4]),'little')
    if 0x02000000<=p<0x02400000:
        t=s(p)
        if t not in log[-3:]:log.append(t)
    return 1
mem.register_exec(0x02033f2c,on)
W=[]
def onw(a,sz):
    if len(W)<6:
        W.append(1);open('work/lzsrc.bin','wb').write(bytes(mem.unsigned[reg.r0:reg.r0+96]));log.append('WRITE pc=%x lr=%x r0=%x r1=%x r2=%x'%(reg.r15,reg.r14,reg.r0,reg.r1,reg.r2))
    return 1
mem.register_write(0x021833AC,onw,64)
for t in seq.split(','):
    if t.startswith('w'):emu.run(int(t[1:]))
    elif t[0]=='T':
        x,y=map(int,t[1:].split(':'));emu.e.input.touch_set_pos(x,y);emu.run(8);emu.e.input.touch_release();emu.run(40)
    elif t: log.append('-- '+t);emu.press(emutest.KEYS[t],after=50)
emu.run(30)
print('LOG',*log,sep='\nLOG ')
emutest.shutdown()
