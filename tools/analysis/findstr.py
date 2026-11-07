import pathlib,sys
sys.path.insert(0,'tools')
from scan_msg import lz10
pats={'チップフォルダ':bytes([0x1E,0x5B,0x52,0x28,0x57,0x32,0x48]),'セーブ':bytes([0x15,0x82,0x4E]),'キーアイテム':bytes([0x14,0x82,0x0C,0x0D,0x1A,0x2C])}
for root in ('work/jp/fs','work/jp/overlay'):
    for f in pathlib.Path(root).rglob('*'):
        if not f.is_file():continue
        b=f.read_bytes()
        for y in (b,lz10(b)):
            if not y:continue
            for k,p in pats.items():
                if p in y and k!='セーブ':print(f,k,hex(y.find(p)),len(y))
a=open('work/jp/arm9.bin','rb').read()
for k,p in pats.items():
    i=a.find(p);print(k,hex(0x02000000+i) if i>=0 else None)
