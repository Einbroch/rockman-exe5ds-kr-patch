import pathlib,sys,collections
sys.path.insert(0,'tools')
from scan_msg import lz10
v=open('work/v_bgb.bin','rb').read()
pieces=[v[o:o+64] for o in range(0xA000,0x18000,0x400) if len(set(v[o:o+64]))>8]
print(len(pieces))
c=collections.Counter()
for f in pathlib.Path('work/jp/fs').rglob('*'):
    if not f.is_file():continue
    d=f.read_bytes();x=lz10(d) or d
    for p in pieces:
        if p in x:c[f.name]+=1
print(c.most_common(10))
a=open('work/jp/arm9.bin','rb').read()
print('arm9',sum(p in a for p in pieces))
for f in sorted(pathlib.Path('work/jp/overlay').glob('*.bin')):
    b=f.read_bytes()
    n=sum(p in b for p in pieces)
    if n:print(f.name,n,len(b))
# 대사 슬롯처럼 RAM 전체에서 찾기
r=open('work/ram_p3.bin','rb').read()
print('ram',[hex(0x02000000+r.find(p)) for p in pieces[:6]])
