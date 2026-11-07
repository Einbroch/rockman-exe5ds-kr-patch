import struct
from PIL import Image
A='work/jp/fs/data/rom/a/'
for pix in ('result00.pix',):
    d=open(A+pix,'rb').read();print(pix,len(d))
import glob
for f in sorted(glob.glob(A+'result*')+glob.glob(A+'res*')):print(f[-14:],len(open(f,'rb').read()))
