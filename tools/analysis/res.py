import struct
from PIL import Image,ImageDraw
A='work/jp/fs/data/rom/a/'
o=Image.new('RGB',(3*(24*16+6),18*16+10),(60,0,0))
for k,(p,s) in enumerate((('result00.pix','result0.srn'),('result01.pix','result1.srn'),('result02.pix','result2.srn'))):
    c=open(A+p,'rb').read();m=open(A+s,'rb').read()
    e=struct.unpack('<432H',m)
    print(p,len(c)//32,max(x&1023 for x in e),min(x&1023 for x in e),sorted({x>>12 for x in e}),m[:8].hex(), sum(1 for x in e if x&0xC00))
    base=min(x&1023 for x in e if x&1023)
    im=Image.new('L',(24*8,18*8))
    for i,v in enumerate(e):
        t=(v&1023);hf=(v>>10)&1;vf=(v>>11)&1
        off=(t-1)*32
        if t==0: continue
        if off+32>len(c):continue
        for y in range(8):
            for x in range(8):
                q=(c[off+y*4+x//2]>>(4*(x&1)))&15
                im.putpixel(((i%24)*8+(7-x if hf else x),(i//24)*8+(7-y if vf else y)),q*17)
    im=im.resize((24*16,18*16),0).convert('RGB');d=ImageDraw.Draw(im)
    for x in range(0,192,32):d.text((x*2,0),str(x),fill=(255,255,0))
    for y in range(0,144,16):d.text((0,y*2),str(y),fill=(0,255,0))
    o.paste(im,(k*(24*16+6),0))
o.resize((o.width*2//3,o.height*2//3),0).save('work/t.png');print(o.size)
