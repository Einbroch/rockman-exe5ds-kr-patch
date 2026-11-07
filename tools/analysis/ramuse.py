import sys,os
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
emu=emutest.Emu('work/orig.nds',sys.argv[1])
ram=bytes(emu.e.memory.unsigned[0x02000000:0x02400000])
# 64KB 단위 0 비율
p=None
for a in range(0,0x400000,0x10000):
    b=ram[a:a+0x10000];z=b.count(0)*100//0x10000
    print(hex(0x02000000+a),z,'%',end='  ')
    if a%0x40000==0x30000:print()
open('work/ram_%s.bin'%sys.argv[1],'wb').write(ram)
emutest.shutdown()
