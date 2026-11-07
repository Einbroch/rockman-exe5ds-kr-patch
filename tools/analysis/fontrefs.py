import struct,glob
lo,hi=0x0210F224,0x02127784
rows=[]
for f in ['work/jp/arm9.bin']+sorted(glob.glob('work/jp/overlay/*.bin')):
    d=open(f,'rb').read()
    for o in range(0,len(d)-3,4):
        v=struct.unpack_from('<I',d,o)[0]
        if lo<=v<hi+0x1200: rows.append((f[-8:],o,hex(v)))
import collections
c=collections.Counter(r[2] for r in rows)
print(len(rows));print(sorted(c.items()))
for r in rows:
    if r[0]=='arm9.bin' or True:
        pass
print([ (r[0],hex(r[1]),r[2]) for r in rows][:60])
