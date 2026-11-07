from PIL import Image
d=open('work/jp/arm9.bin','rb').read()
def sheet(off,n,w,h,bw,name,cols=32,sc=2):
    H=(n+cols-1)//cols
    im=Image.new('RGB',(cols*(w+1)*sc,H*(h+1)*sc),(40,40,90))
    pal=[(255,255,255),(0,0,0),(120,120,255),(255,0,0)]+[(0,255,0)]*12
    for i in range(n):
        g=d[off+i*bw:off+(i+1)*bw];st=len(g)//h
        for y in range(h):
            for x in range(w):
                b=g[y*st+x//2];v=(b>>(4*(x&1)))&15
                for a in range(sc):
                    for c in range(sc):
                        im.putpixel(((i%cols)*(w+1)*sc+x*sc+a,(i//cols)*(h+1)*sc+y*sc+c),pal[v])
    im.save('work/'+name)
sheet(0x10f224,441,16,12,0x60,'f12.png')
sheet(0x119784,448,8,16,0x40,'f8.png',cols=40)
sheet(0x120784,448,8,16,0x40,'fs.png',cols=40)
