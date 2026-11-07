import sys,struct
from PIL import Image,ImageDraw
sys.path.insert(0,'tools')
from scan_msg import lz10
R='work/jp/fs/data/rom/'
L=[('b/b_submenu01.pix','b/b_submenu01.srn',32),('b/c_trader_bg_lz.bin','a/c_trader_bg_lz.srn',32)]
ims=[]
for pf,sf,W in L:
    c=open(R+pf,'rb').read();c=lz10(c) or c
    m=open(R+sf,'rb').read();m=lz10(m) or m
    print(pf,len(c),len(m),m[:12].hex())
    hd=0
    e=struct.unpack('<%dH'%((len(m)-hd)//2),m[hd:])
    b=min(x&1023 for x in e if x&1023)
    print(hex(b),max(x&1023 for x in e),len(c)//32)
    H=len(e)//W+1
    im=Image.new('L',(W*8,H*8),0)
    for i,v in enumerate(e):
        t=(v&1023)-b;hf=(v>>10)&1;vf=(v>>11)&1
        for y in range(8):
            for x in range(8):
                o=t*32+y*4+x//2
                if o<0 or o>=len(c):continue
                q=(c[o]>>(4*(x&1)))&15
                im.putpixel(((i%W)*8+(7-x if hf else x),(i//W)*8+(7-y if vf else y)),q*17)
    ims.append(im.resize((im.width*2,im.height*2),0))
o=Image.new('L',(512,sum(i.height for i in ims)+8),90);y=0
for i in ims:o.paste(i,(0,y));y+=i.height+4
o.save('work/t.png');print(o.size)
