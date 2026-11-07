import sys
from PIL import Image
sys.path.insert(0,'tools')
from scan_msg import lz10
f=sys.argv[1];d=open(f,'rb').read();x=lz10(d) or d
n=len(x)//32//8;cols=10
im=Image.new('L',(cols*34,((n+cols-1)//cols)*18),30)
for k in range(n):
    for t in range(8):
        i=k*8+t
        for y in range(8):
            for xx in range(8):
                q=x[i*32+y*4+xx//2];v=(q>>(4*(xx&1)))&15
                im.putpixel(((k%cols)*34+(t%4)*8+xx,(k//cols)*18+(t//4)*8+y),v*17)
im=im.resize((im.width*2,im.height*2),0);im.save(sys.argv[2]);print(n,im.size)
