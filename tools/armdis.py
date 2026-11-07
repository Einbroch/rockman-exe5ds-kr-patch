#!/usr/bin/env python3
"""썸/ARM 역어셈. 사용법: dis.py 시작 끝 [arm] """
import sys,capstone
d=open('work/jp/arm9.bin','rb').read()
a=int(sys.argv[1],16);b=int(sys.argv[2],16)
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM if len(sys.argv)>3 else capstone.CS_MODE_THUMB)
md.skipdata=True
o=a-0x02000000
for i in md.disasm(d[o:b-0x02000000],a):
    x=''
    if 'pc' in i.op_str and i.mnemonic.startswith('ldr') and '#' in i.op_str:
        try:
            im=int(i.op_str.split('#')[-1].rstrip(']'),0);t=((i.address+4)&~3)+im
            x=' ; =0x%08x'%int.from_bytes(d[t-0x02000000:t-0x02000000+4],'little')
        except:pass
    print('%08x %-10s %-8s %s%s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str,x))
