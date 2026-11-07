import sys,os,struct,collections
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
emu=emutest.Emu('build/exe5ds_ko.nds','k2_end')
mem=emu.e.memory;reg=mem.register_arm9
c=collections.Counter()
def mk(tag):
    def on(a,s):
        c[(tag,hex(reg.r15),hex(reg.r14))]+=1
        return 1
    return on
for k in []:
    if k[0]=='w':emu.run(int(k[1:]))
    else:emu.press(emutest.KEYS[k],after=60)
mem.register_read(0x020d7874,mk('fold'),84)
mem.register_read(0x02120784,mk('sub'),0x7000)
mem.register_read(0x02119784,mk('f8'),0x7000)
mem.register_read(0x0212c848,mk('chipname'),2429)
mem.register_read(0x0212b388,mk('inf1'),300)
[emu.press(emutest.KEYS[k],after=70) for k in ('ST','A','A')];emu.run(100)
for k,v in c.most_common(30):print(k,v)
emutest.shutdown()
