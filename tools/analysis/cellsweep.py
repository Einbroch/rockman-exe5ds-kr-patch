"""패치본의 모든 OBJ 셀을 쪽 시트로 깐다(남은 일본어 찾기): cellsweep.py 롬"""
import hashlib, os, re, struct, sys
sys.path.insert(0, 'tools')
import ncer, ndspy.rom
from scan_msg import lz10
from PIL import Image, ImageDraw
r = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
names = {}
for fid, _ in enumerate(r.files):
    p = r.filenames.filenameOf(fid)
    if p and p.startswith('data/rom/dc/'):
        names[p.split('/')[-1]] = fid
pre = sorted(n[:-len('g_lz.bin')] for n in names if n.endswith('g_lz.bin'))
pre2 = []
seen = set()
items = []
for p in pre:
    if p + 'c_lz.bin' not in names:
        continue
    g = lz10(bytes(r.files[names[p + 'g_lz.bin']]))
    c = lz10(bytes(r.files[names[p + 'c_lz.bin']]))
    if not g or not c or c[:4] != b'RECN':
        continue
    d = g[0x30:]
    try:
        cs = ncer.cells(c)
    except Exception:
        continue
    for i, cell in enumerate(cs):
        if not cell:
            continue
        xs = min(q['x'] for q in cell)
        ys = min(q['y'] for q in cell)
        W = max(q['x'] + q['w'] for q in cell) - xs
        H = max(q['y'] + q['h'] for q in cell) - ys
        if W > 200 or H > 200 or W < 16:
            continue
        im = Image.new('L', (W, H), 30)
        for q in cell:
            tw = q['w'] // 8
            b8 = q.get('d8')
            step = 64 if b8 else 32
            for j in range(tw * q['h'] // 8):
                o = q['tile'] * 32 + j * step
                cx, cy = q['x'] - xs + j % tw * 8, q['y'] - ys + j // tw * 8
                for y in range(8):
                    for x in range(8):
                        k = o + y * 8 + x if b8 else o + y * 4 + x // 2
                        if k < len(d):
                            v = d[k] if b8 else ((d[k] >> (4 * (x & 1))) & 15) * 17
                            if v:
                                im.putpixel((cx + x, cy + y), min(v + 40, 255))
        h = hashlib.md5(im.tobytes()).digest()
        ink = sum(1 for v in im.getdata() if v > 60)
        if h in seen or ink < 12:
            continue
        seen.add(h)
        items.append((f'{p}.{i}', im))
print(len(items))
PW, PH = 1500, 1050
pg = []
cur = Image.new('L', (PW, PH), 0)
dr = ImageDraw.Draw(cur)
x = y = rowh = 0
n = 0
for name, im in items:
    w, h = im.size[0] + 4, im.size[1] + 12
    if x + w > PW:
        x = 0
        y += rowh + 2
        rowh = 0
    if y + h > PH:
        cur.save(f'work/sw_{n:02d}.png')
        n += 1
        cur = Image.new('L', (PW, PH), 0)
        dr = ImageDraw.Draw(cur)
        x = y = rowh = 0
    cur.paste(im, (x, y + 10))
    dr.text((x, y), name.replace('_', ''), fill=255)
    x += max(w, 44)
    rowh = max(rowh, h)
cur.save(f'work/sw_{n:02d}.png')
print(n + 1)
