import sys,glob,os
from PIL import Image,ImageDraw
sys.path.insert(0,'tools')
from scan_msg import lz10
names=sys.argv[2:];cols=int(sys.argv[1])
ims=[]
for n in names:
    f=glob.glob(f'work/jp/fs/data/rom/*/{n}')[0]
    b=open(f,'rb').read();x=lz10(b) or b
    base=0x30 if x[:4]==b'RGCN' else (4 if n.startswith('icon4') and x[:1]==b'\0' else 0)
    tn=(len(x)-base)//32
    H=(tn+31)//32
    im=Image.new('L',(32*8,H*8+10),30)
    ImageDraw.Draw(im).text((0,0),n,fill=255)
    for i in range(tn):
        for y in range(8):
            for xx in range(8):
                q=x[base+i*32+y*4+xx//2];v=(q>>(4*(xx&1)))&15
                im.putpixel(((i%32)*8+xx,10+(i//32)*8+y),v*17)
    ims.append(im)
W=256*cols+4*cols
rows=[ims[i:i+cols] for i in range(0,len(ims),cols)]
H=sum(max(i.height for i in r)+2 for r in rows)
o=Image.new('L',(W,H),60);y=0
for r in rows:
    x=0
    for i in r:o.paste(i,(x,y));x+=260
    y+=max(i.height for i in r)+2
o=o.resize((o.width*2,o.height*2),0);o.save('work/t.png');print(o.size)
