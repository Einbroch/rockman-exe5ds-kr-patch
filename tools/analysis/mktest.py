"""시험 롬 만들기: mktest.py 원본 출력 바이트열hex  → plugin 플래그 건너뜀 + plugout 스크립트 시작을 지정 바이트로"""
import ndspy.rom,struct,sys
src,dst,h=sys.argv[1:4]
payload=bytes.fromhex(h)
raw=bytearray(open(src,'rb').read())
r=ndspy.rom.NintendoDSRom(bytes(raw))
fat=int.from_bytes(raw[0x48:0x4C],'little')
def put(fid,d):
    s=int.from_bytes(raw[fat+fid*8:fat+fid*8+4],'little');e=int.from_bytes(raw[fat+fid*8+4:fat+fid*8+8],'little')
    assert e-s==len(d);raw[s:e]=d
fid=r.filenames.idOf('data/rom/a/plugin.msg');d=bytearray(r.files[fid])
i=d.find(bytes([0xEF,0x00,0x40,0x05,0x00,0xFF]));d[i+5]=0;put(fid,d)
fid=r.filenames.idOf('data/rom/a/plugout.msg');d=bytearray(r.files[fid])
n=struct.unpack_from('<H',d)[0]//2
for o in set(struct.unpack_from('<%dH'%n,d)):
    if o+len(payload)<=len(d):d[o:o+len(payload)]=payload
put(fid,d)
open(dst,'wb').write(raw)
