import sys
sys.argv=['x','bg0000']
exec(open('tools/analysis/bgs.py',encoding='utf8').read().split("if len(sys.argv) > 1:")[0])
from PIL import ImageDraw
spec=[('bg0100',0,168,256,24),('bg0301',0,0,256,24),('bg0301',0,168,256,24),('bg1501',0,0,256,24),('bg1501',0,168,256,24),('bg0600',0,0,128,24),('bg1300',0,0,128,24),('bg1200',0,20,100,60),('bg0401',0,0,256,50),('bg1701',0,0,256,50),('bg1700',0,144,256,48),('bg0002',160,100,96,92)]
rows=[]
for n,x,y,w,h in spec:
    a=render(n).crop((x,y,x+w,y+h)).convert('RGB').resize((w*3,h*3),0)
    d=ImageDraw.Draw(a)
    for gx in range((x+7)//8*8,x+w,8):
        d.line([( (gx-x)*3,0),((gx-x)*3,2)],fill=(255,255,0))
        if gx%32==0: d.text(((gx-x)*3+1,3),str(gx),fill=(255,255,0))
    for gy in range((y+7)//8*8,y+h,8):
        d.line([(0,(gy-y)*3),(2,(gy-y)*3)],fill=(0,255,0))
        if gy%16==0: d.text((3,(gy-y)*3),str(gy),fill=(0,255,0))
    d.text((a.width-48,0),n,fill=(0,255,255))
    rows.append(a)
H=sum(r.height+2 for r in rows)
o=Image.new('RGB',(770,H),(80,0,0))
y=0
for r in rows:
    o.paste(r,(0,y));y+=r.height+2
o.save('work/t.png');print(o.size)
