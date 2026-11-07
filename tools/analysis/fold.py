import sys,os,struct
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
emu=emutest.Emu('build/exe5ds_ko.nds','k2_end')
mem=emu.e.memory
for k in 'ST,w60,A,w60,A,w180'.split(','):
    if k[0]=='w':emu.run(int(k[1:]))
    else:emu.press(emutest.KEYS[k],after=60)
emu.shot('fold0')
ram=bytes(mem.unsigned[0x02000000:0x02400000])
vram=bytes(mem.unsigned[0x06000000:0x06020000]) if False else b''
pat=bytes([0x28,0x57,0x32,0x48])
i=ram.find(pat)
while i>=0:
    print(hex(0x02000000+i),ram[i-8:i+12].hex());i=ram.find(pat,i+1)
open('work/ram_fold.bin','wb').write(ram)
emutest.shutdown()
