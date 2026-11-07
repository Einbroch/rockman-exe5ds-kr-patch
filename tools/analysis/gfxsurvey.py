"""그림 파일 썸네일 시트. 사용법: gfxsurvey.py 쪽번호 → work/t.png (쪽당 파일 수 고정)"""
import glob
import os
import pathlib
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, 'tools')
from scan_msg import lz10  # noqa: E402

PICK = re.compile(r'^(?:[bk]_)?(result|coresult|rop_|libe_|strategy|gameover|ev_chipname|nameentry|sort|submenu|movemap|movepic|number_bg|'
                  r'oyabg|subscrn|chiphen|panel|custom|cus_g|sub_kind|collabo_(?:menu|manual|entry|cross)|c_trader|bug_tr|cross_tr|'
                  r'gchabg|frame|infobg|infomess|kaizou|keyitem|linkerr|m_shutter|mapname|mapicon|minigame|navichg|navirun|navicus|'
                  r'new|operationbg|pause|rock_bg|savebg|shop|shuffle|subrock|t_license|icon|n_data|b_data|k_data|data0|hp|atk|'
                  r'chip_|chipdata|bug|card|unicard|zeni|ndts|nodt|sf_nds|cpdt|opbt|pl_|navi_mark|rfumark|ojama|load)')
files = []
for d in 'a b k c pet'.split():
    for f in sorted(glob.glob(f'work/jp/fs/data/rom/{d}/*')):
        n = os.path.basename(f)
        if n.endswith(('.clt', '.srn', '.msg')) or '_srn' in n or '_clt' in n or 'LZ.bin' in n and 'set' in n:
            continue
        if not PICK.match(n):
            continue
        b = open(f, 'rb').read()
        x = lz10(b) or b
        if len(x) < 256 or len(x) > 80000:
            continue
        files.append((f, x))
print(len(files))
PAGE = 48
page = int(sys.argv[1])
cols, cw, ch = 6, 258, 100
sel = files[page * PAGE:(page + 1) * PAGE]
im = Image.new('L', (cols * cw, ((len(sel) + cols - 1) // cols) * ch), 30)
d = ImageDraw.Draw(im)
for k, (f, x) in enumerate(sel):
    bx, by = (k % cols) * cw, (k // cols) * ch
    d.text((bx + 1, by), os.path.basename(f)[:30] + f' {len(x)}', fill=255)
    base = 0x30 if x[:4] == b'RGCN' else 0
    n = (len(x) - base) // 32
    for i in range(min(n, 32 * 11)):
        for y in range(8):
            for xx in range(8):
                q = x[base + i * 32 + y * 4 + xx // 2]
                v = (q >> (4 * (xx & 1))) & 15
                im.putpixel((bx + (i % 32) * 8 + xx, by + 11 + (i // 32) * 8 + y), v * 17)
im.save('work/t.png')
print(im.size, len(sel))
