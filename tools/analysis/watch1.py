import sys,os,collections
sys.path.insert(0,'tools')
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import emutest
emu=emutest.Emu('work/orig.nds','i2_end')
mem=emu.e.memory;reg=mem.register_arm9
font=open('work/jp/fs/data/rom/a/font12x12.pix','rb').read()
ram=bytes(mem.unsigned[0x02000000:0x02400000])
sig=font[0x600:0x640]
hits=[]
i=ram.find(sig)
while i>=0: hits.append(0x02000000+i-0x600);i=ram.find(sig,i+1)
print('font in RAM',[hex(x) for x in hits])
script=b'\xe8\x00'
# 현재 메시지 후보: dm0700 없음, 파일 전체에서 RAM 스크립트 찾기 생략
c=collections.Counter()
log=[]
if hits:
    base=hits[0]
    def on(a,s):
        k=(reg.r15,reg.r14)
        if not c[k]: log.append((hex(a),hex(reg.r15),hex(reg.r14),[hex(getattr(reg,'r%d'%i)) for i in range(13)]))
        c[k]+=1
        return 1
    for a in range(base,base+len(font),4): pass
    mem.register_read(base,on,len(font))
for i in range(6):
    emu.press(emutest.Keys.KEY_A,after=80)
for k,v in c.most_common(20):print(hex(k[0]),hex(k[1]),v)
for l in log[:6]:print(l)
emu.shot('w1');
emutest.shutdown()
