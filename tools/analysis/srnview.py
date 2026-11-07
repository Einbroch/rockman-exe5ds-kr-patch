import sys,struct
from PIL import Image,ImageDraw
sys.path.insert(0,'tools')
from scan_msg import lz10
R='work/jp/fs/data/rom/'
L=[('b/b_submenu01.pix','b/b_submenu01.srn'),('b/b_sort_lz.bin','a/sort_lz.srn')]
ims=[]
for pf,sf in L:
    c=open(R+pf,'rb').read();c=lz10(c) or c
    m=open(R+sf,'rb').read();m=lz10(m) or m
    print(pf,len(c),len(m),m[:12].hex())
    e=struct.unpack('<%dH'%(len(m)//2),m)
    W=32;H=len(e)//W
    print(H,max(x&1023 for x in e),sorted({x>>12 for x in e}))
    im=Image.new('L',(W*8,H*8),0)
    for i,v in enumerate(e):
        t=v&1023;hf=(v>>10)&1;vf=(v>>11)&1
        for y in range(8):
            for x in range(8):
                o=t*32+y*4+x//2
                if o>=len(c):continue
                q=(c[o]>>(4*(x&1)))&15
                im.putpixel(((i%W)*8+(7-x if hf else x),(i//W)*8+(7-y if vf else y)),q*17)
    im=im.resize((im.width*3,im.height*3),0).convert('RGB')
    d=ImageDraw.Draw(im)
    for x in range(0,W*8,32):d.text((x*3,0),str(x),fill=(255,255,0))
    for y in range(0,H*8,16):d.text((0,y*3),str(y),fill=(0,255,0))
    ims.append(im)
o=Image.new('RGB',(768,sum(i.height for i in ims)+6),(90,0,0));y=0
for i in ims:o.paste(i,(0,y));y+=i.height+6
o.save('work/t.png');print(o.size)
