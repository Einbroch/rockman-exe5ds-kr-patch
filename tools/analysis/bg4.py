import sys,struct
from PIL import Image,ImageDraw
sys.path.insert(0,'tools')
import ncer
B='work/jp/fs/data/rom/db/'
def render(n,chn=None):
    c=ncer.unpack(B+(chn or n)+'_ch_lz.bin');s=ncer.unpack(B+n+'_sc_lz.bin')
    m=struct.unpack_from('<1024H',s,0x24)
    im=Image.new('L',(256,256))
    for i,e in enumerate(m):
        t=e&1023;hf=(e>>10)&1;vf=(e>>11)&1
        o=0x30+t*32
        if o+32>len(c):continue
        for y in range(8):
            for x in range(8):
                v=(c[o+y*4+x//2]>>(4*(x&1)))&15
                im.putpixel(((i%32)*8+(7-x if hf else x),(i//32)*8+(7-y if vf else y)),v*17)
    return im
ns=sys.argv[1:]
o=Image.new('RGB',(len(ns)*400,520),(60,0,0))
for k,n in enumerate(ns):
    a=render(n).crop((60,0,190,173)).convert('RGB').resize((390,519),0)
    d=ImageDraw.Draw(a);d.text((300,2),n,fill=(0,255,255))
    for x in range(64,190,16):d.text(((x-60)*3,0),str(x),fill=(255,255,0))
    for y in range(0,173,16):d.text((0,y*3),str(y),fill=(0,255,0))
    o.paste(a,(k*400,0))
o.save('work/t.png');print(o.size)
