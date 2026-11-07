import json,re,struct,glob,os
a9=open('work/jp/arm9.bin','rb').read()
ram=open('work/ram_i2_end.bin','rb').read()
pop=json.load(open('work/population.json',encoding='utf8'))
names=re.findall(rb'[\x5c]([a-z]+)[\x5c]([a-zA-Z0-9_.]+)',a9)
S={(a.decode(),b.decode()) for a,b in names}
print('경로 문자열',len(S))
ex=0;em=[]
for n,v in pop.items():
    p=v['path'].split('/');key=(p[2],p[3])
    d=open(f'work/msg/{n}.msg','rb').read()
    i=a9.find(d) if len(d)>30 else -1
    inS=key in S
    if i>=0: em.append((n,hex(0x02000000+i),len(d),inS))
    ex+=inS
print('경로표에 있는 것',ex,'/',len(pop))
print('ARM9 내장',len(em),sum(e[2] for e in em));print(em)
for f in glob.glob('work/jp/fs/data/rom/*/*'):
    if not re.search(r'font|moji',f):continue
    b=open(f,'rb').read()
    if len(b)<64:continue
    s=b[len(b)//2:len(b)//2+64];i=a9.find(s);j=ram.find(s)
    print(os.path.basename(f),len(b),hex(i+0x02000000-len(b)//2) if i>=0 else None,hex(j+0x02000000-len(b)//2) if j>=0 else None, (os.path.basename(f.replace(chr(92),'/').split('/')[-2]),os.path.basename(f)) in S)
