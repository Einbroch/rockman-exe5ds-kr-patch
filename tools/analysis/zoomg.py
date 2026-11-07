import sys,glob
from PIL import Image,ImageDraw
sys.path.insert(0,'tools')
from scan_msg import lz10
n=sys.argv[1];W=int(sys.argv[2]);S=int(sys.argv[3]);base=int(sys.argv[4]) if len(sys.argv)>4 else 0
f=glob.glob(f'work/jp/fs/data/rom/*/{n}')[0]
b=open(f,'rb').read();x=lz10(b) or b
print(len(x),x[:8].hex())
x=x[base:]
tn=len(x)//32;H=(tn+W-1)//W
im=Image.new('RGB',(W*8*S,H*(8*S+1)),(40,0,60))
for i in range(tn):
    for y in range(8):
        for xx in range(8):
            q=x[i*32+y*4+xx//2];v=(q>>(4*(xx&1)))&15
            for a in range(S):
                for c in range(S):
                    im.putpixel(((i%W)*8*S+xx*S+a,(i//W)*(8*S+1)+y*S+c),(v*17,v*17,v*17))
d=ImageDraw.Draw(im)
for i in range(0,W,4):
    d.text((i*8*S,0),str(i),fill=(255,255,0))
for r in range(H):
    d.text((0,r*(8*S+1)),str(r*W),fill=(0,255,0))
im.save('work/t.png');print(im.size)
