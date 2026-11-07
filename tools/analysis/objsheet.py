import sys
from PIL import Image
sys.path.insert(0,'tools')
from scan_msg import lz10
f=sys.argv[1];pf=sys.argv[2];tw=int(sys.argv[3]);th=int(sys.argv[4]);cols=int(sys.argv[5]);skip=int(sys.argv[6]) if len(sys.argv)>6 else 0
d=open(f,'rb').read();x=lz10(d) or d
p=open(pf,'rb').read();p=lz10(p) or p
pal=[(((c&31)*8),(((c>>5)&31)*8),(((c>>10)&31)*8)) for c in [p[i]|p[i+1]<<8 for i in range(0,min(len(p),32),2)]]
pal[0]=(60,60,60)
n=(len(x)//32-skip)//(tw*th)
rows=(n+cols-1)//cols
im=Image.new('RGB',(cols*(tw*8+2),rows*(th*8+2)),(0,0,0))
for k in range(n):
    bx=(k%cols)*(tw*8+2);by=(k//cols)*(th*8+2)
    for t in range(tw*th):
        i=skip+k*tw*th+t
        for y in range(8):
            for xx in range(8):
                b=x[i*32+y*4+xx//2];v=(b>>(4*(xx&1)))&15
                im.putpixel((bx+(t%tw)*8+xx,by+(t//tw)*8+y),pal[v])
im=im.resize((im.width*2,im.height*2),0);im.save('work/t.png');print(n,im.size)
