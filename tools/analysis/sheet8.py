import sys
from PIL import Image
sys.path.insert(0,'tools')
from scan_msg import lz10
f=sys.argv[1];w=int(sys.argv[2]);
d=open(f,'rb').read();x=lz10(d) or d
print(len(d),len(x),d[:8].hex())
pal=None
if len(sys.argv)>3:
    p=open(sys.argv[3],'rb').read();p=lz10(p) or p
    pal=[(((c&31)*8),(((c>>5)&31)*8),(((c>>10)&31)*8)) for c in [p[i]|p[i+1]<<8 for i in range(0,min(len(p),512),2)]]
n=len(x)//64;h=(n+w-1)//w
im=Image.new('RGB',(w*8,h*8))
for i in range(n):
    for y in range(8):
        for xx in range(8):
            v=x[i*64+y*8+xx]
            im.putpixel(((i%w)*8+xx,(i//w)*8+y),pal[v] if pal and v<len(pal) else (v,v,v))
im.save('work/t.png');print(n,im.size)
