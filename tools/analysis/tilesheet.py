import sys
from PIL import Image
sys.path.insert(0,'tools')
from scan_msg import lz10
f=sys.argv[1];w=int(sys.argv[2]) if len(sys.argv)>2 else 32
d=open(f,'rb').read();x=lz10(d) or d
off=int(sys.argv[3],0) if len(sys.argv)>3 else 0
x=x[off:]
n=len(x)//32;h=(n+w-1)//w
im=Image.new('L',(w*8,h*8))
for i in range(n):
    for y in range(8):
        for xx in range(8):
            b=x[i*32+y*4+xx//2];v=(b>>(4*(xx&1)))&15
            im.putpixel(((i%w)*8+xx,(i//w)*8+y),v*17)
im=im.resize((im.width*2,im.height*2),0);im.save(sys.argv[4] if len(sys.argv)>4 else 'work/t.png');print(n,im.size)
