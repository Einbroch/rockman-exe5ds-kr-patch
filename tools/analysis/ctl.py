import struct,re,glob,collections
d=open('work/jp/arm9.bin','rb').read()
t=0x02130cb8-0x02000000
tab=struct.unpack_from('<27I',d,t)
for i,v in enumerate(tab):print(hex(0xE5+i),hex(v))
ini=open('external/textpet-plugins/mmbn5ds.ini',encoding='utf8').read()
bases=collections.Counter(re.findall(r'(?m)^base = ([0-9A-F]{2})',ini))
print('db',sorted(bases.items()))
ini=open('external/textpet-plugins/mmbn5s.ini',encoding='utf8').read()
print('dbs',sorted(collections.Counter(re.findall(r'(?m)^base = ([0-9A-F]{2})',ini)).items()))
# 명령 사용 빈도
c=collections.Counter();H=collections.Counter()
for f in glob.glob('work/tpl/*.tpl'):
    t=open(f,encoding='utf8').read()
    H[len(re.findall(r'(?m)^script \d+ mmbn5s ',t))>0]+=1
    for m in re.findall(r'(?m)^\t([a-zA-Z_][\w]*)$',t):c[m]+=1
print(H,len(c));print(c.most_common(70))
