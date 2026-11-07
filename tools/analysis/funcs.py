import struct,sys
d=open('work/jp/arm9.bin','rb').read()
def calls(t):
    r=[]
    for o in range(0,0x156c80-4,2):
        h1,h2=struct.unpack_from('<HH',d,o)
        if h1&0xF800==0xF000 and h2&0xE800==0xE800:
            off=((h1&0x7FF)<<12)|((h2&0x7FF)<<1)
            if off&0x400000:off-=0x800000
            pc=0x02000000+o+4
            tg=pc+off
            if h2&0xF800==0xE800: tg&=~3   # blx
            if tg==t:r.append(0x02000000+o)
    return r
def lits(t):
    p=struct.pack('<I',t|1);L=[];i=d.find(p)
    while i>=0:
        L.append(0x02000000+i);i=d.find(p,i+1)
    return L
for a in sys.argv[1:]:
    t=int(a,16);print(a,'calls',[hex(x) for x in calls(t)][:24],len(calls(t)),'lits',[hex(x) for x in lits(t)][:24])
