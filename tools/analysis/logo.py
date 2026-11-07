import struct,sys
from PIL import Image
sys.path.insert(0,'tools')
from scan_msg import lz10
A='work/jp/fs/data/rom/a/'
c=open(A+'title.bin','rb').read();m=open(A+'title00.srn','rb').read();p=open(A+'title00.clt','rb').read()
print(len(c),len(m),len(p),c[:8].hex(),m[:12].hex())
print('8bpp tiles',len(c)/64,'4bpp',len(c)/32,'max',max(struct.unpack('<%dH'%(len(m)//2),m))&1023, sorted({e>>12 for e in struct.unpack('<%dH'%(len(m)//2),m)}))
pal=[((v&31)*8,((v>>5)&31)*8,((v>>10)&31)*8) for v in struct.unpack('<%dH'%(len(p)//2),p)]
M=struct.unpack('<%dH'%(len(m)//2),m)
im=Image.new('RGB',(256,192))
for i,e in enumerate(M):
    t=e&1023;hf=(e>>10)&1;vf=(e>>11)&1
    for y in range(8):
        for x in range(8):
            v=c[t*64+y*8+x]
            im.putpixel(((i%32)*8+(7-x if hf else x),(i//32)*8+(7-y if vf else y)),pal[v])
im.resize((768,576),0).save('work/z.png')
