#!/usr/bin/env python3
"""ARM9 한글 엔진. 전부 ARM9 크기를 바꾸지 않고 제자리에서 고친다.

공간(폰트·폭 표의 꼬리는 idx >= KEEP 칸이라 쓰이지 않게 된다):
  W1 0x020E00EC~0x020E038C  폭 표 1 꼬리: 스텁
  W2 0x020E07D0~0x020E0A70  폭 표 2 꼬리: 예비
  T1 0x02115884~0x02119784  12×12 폰트 꼬리: 버퍼 + 12×12 한글 앞부분
  T2 0x0211DBC4~0x02120784  8×16 폰트 꼬리: 12×12 한글 뒷부분 + 8×16 한글 앞부분
  T3 0x02124BC4~0x02127784  subfont 꼬리: 8×16 한글 뒷부분
"""
import struct

import keystone

ARM9 = 0x02000000
KEEP = 0x111                # idx 이 미만은 폰트에 제자리로 남는다(E4 00~2C 까지)
F12, F8, FS = 0x0210F224, 0x02119784, 0x02120784
W1 = 0x020DFCA8
W2 = 0x020E038C
STUB = (W1 + KEEP * 4, W2)
SPARE = (W2 + KEEP * 4, W2 + 441 * 4)
T1 = (F12 + KEEP * 0x60, F8)
T2 = (F8 + KEEP * 0x40, FS)
T3 = (FS + KEEP * 0x40, 0x02127784)
BUF = T1[0]                 # 0x60 + 0x40 바이트
BUFSIZE = 0xA0
P12, P16 = 18, 14           # 한글 1벌 크기
HANGUL_W = 12
NOP = bytes.fromhex('c046')

STUBS = r'''
    b ko_dec_r4
    b ko_dec_r0
    b ko_g12
    b ko_gb
    b ko_g16
    b ko_tile
ko_dec_r4:
    push {r2, r3}
    ldrb r2, [r4, #1]
    b dec
ko_dec_r0:
    push {r2, r3}
    ldrb r2, [r0, #1]
dec:
    cmp r1, #0xe4
    bne dec2
    adds r2, #0xe4
    mov r1, r2
    pop {r2, r3}
    bx lr
dec2:
    subs r1, #LEAD0
    movs r3, #SECOND
    muls r1, r3, r1
    adds r1, r1, r2
    movs r3, #0xf2
    lsls r3, r3, #1
    adds r1, r1, r3
    pop {r2, r3}
    bx lr

ko_tile:
    cmp r1, #0xe4
    beq t_e4
    cmp r1, #LEAD0
    bge t_lead
    cmp r1, #0x0b
    blt t_ret
    cmp r1, #0x67
    blt t_dyn
    cmp r1, #0x9a
    bge t_dyn
t_ret:
    bx lr
t_e4:
    adds r0, #1
    ldrb r1, [r0]
    adds r1, #0xe4
    b t_dyn
t_lead:
    adds r0, #1
    push {r2, r3}
    ldrb r2, [r0]
    subs r1, #LEAD0
    movs r3, #SECOND
    muls r1, r3, r1
    adds r1, r1, r2
    movs r3, #0xf2
    lsls r3, r3, #1
    adds r1, r1, r3
    pop {r2, r3}
t_dyn:
    push {r0, r2, r3, r4, r5, r6, r7, lr}
    mov r5, r1
    ldr r7, =TBL
    movs r4, #0
t_s:
    lsls r0, r4, #1
    ldrh r0, [r7, r0]
    cmp r0, r5
    beq t_hit
    adds r4, #1
    cmp r4, #SLOTS
    bne t_s
    movs r0, #0xe0
    ldrh r4, [r7, r0]
    adds r1, r4, #1
    cmp r1, #SLOTS
    bne t_n
    movs r1, #0
t_n:
    strh r1, [r7, r0]
    lsls r0, r4, #1
    strh r5, [r7, r0]
    bl t_addr
    b t_draw
t_hit:
    bl t_addr
    movs r1, #60
t_v:
    ldr r0, [r2, r1]
    ldr r6, [r3, r1]
    cmp r0, r6
    bne t_ok
    subs r1, #4
    bpl t_v
t_draw:
    push {r2}
    mov r1, r5
    ldr r6, =FS
    bl ko_g16
    pop {r2}
    movs r1, #60
t_c:
    ldr r0, [r6, r1]
    str r0, [r2, r1]
    subs r1, #4
    bpl t_c
t_ok:
    bl t_code
    mov r1, r0
    pop {r0, r2, r3, r4, r5, r6, r7, pc}
t_code:
    mov r0, r4
    cmp r0, #92
    blt t_c1
    adds r0, #0x3e
    bx lr
t_c1:
    adds r0, #0x0b
    bx lr
t_addr:
    push {lr}
    bl t_code
    lsls r0, r0, #6
    ldr r2, =VFONT
    adds r2, r2, r0
    ldr r3, =FS
    adds r3, r3, r0
    pop {pc}

ko_g12:
    movs r4, #0xf2
    lsls r4, r4, #1
    cmp r1, r4
    bge g12h
    ldr r4, =F12
    movs r7, #0x60
    muls r7, r1, r7
    adds r7, r7, r4
    ldr r4, =W1
    lsls r1, r1, #2
    ldr r4, [r4, r1]
    bx lr
g12h:
    subs r1, r1, r4
    push {lr}
    bl unpack12
    pop {r0}
    movs r4, #HANGUL_W
    bx r0

ko_gb:
    movs r4, #0xf2
    lsls r4, r4, #1
    cmp r1, r4
    bge gbh
    movs r7, #0x60
    muls r7, r1, r7
    adds r7, r7, r0
    ldr r4, =0x021311dc
    ldrb r6, [r5, #3]
    lsls r6, r6, #2
    ldr r4, [r4, r6]
    lsls r1, r1, #2
    ldr r3, [r4, r1]
    bx lr
gbh:
    subs r1, r1, r4
    push {lr}
    bl unpack12
    pop {r0}
    movs r3, #HANGUL_W
    bx r0

unpack12:
    push {r2, r3, r4, r5, r6, lr}
    movs r2, #P12
    muls r2, r1, r2
    ldr r3, =N12A
    cmp r1, r3
    bge u12b
    ldr r3, =T12A
    b u12c
u12b:
    ldr r3, =T12B
u12c:
    adds r3, r3, r2
    ldr r7, =BUF
    movs r0, #0
    movs r2, #0x60
u12z:
    subs r2, #4
    str r0, [r7, r2]
    bne u12z
    mov r2, r7
    movs r4, #0
u12r:
    movs r5, #0
u12p:
    lsrs r6, r4, #3
    ldrb r6, [r3, r6]
    movs r0, #7
    ands r0, r4
    lsls r6, r0
    movs r0, #0x80
    tst r6, r0
    beq u12n
    lsrs r0, r5, #1
    ldrb r6, [r2, r0]
    movs r1, #1
    ands r1, r5
    lsls r1, r1, #2
    movs r7, #1
    lsls r7, r1
    orrs r6, r7
    strb r6, [r2, r0]
u12n:
    adds r4, #1
    adds r5, #1
    cmp r5, #12
    bne u12p
    adds r2, #8
    cmp r4, #144
    bne u12r
    ldr r7, =BUF
    pop {r2, r3, r4, r5, r6, pc}

ko_g16:
    movs r7, #0xf2
    lsls r7, r7, #1
    cmp r1, r7
    bge g16h
    lsls r7, r1, #6
    adds r6, r6, r7
    bx lr
g16h:
    subs r1, r1, r7
    push {r0, r2, r3, r4, r5, lr}
    mov r5, r6
    push {r5}
    movs r2, #P16
    muls r2, r1, r2
    ldr r3, =N16A
    cmp r1, r3
    bge g16b
    ldr r3, =T16A
    b g16c
g16b:
    ldr r3, =T16B
g16c:
    adds r3, r3, r2
    ldr r7, =BUF2
    movs r6, #0
    movs r4, #0
g16r:
    movs r0, #0
    cmp r4, #1
    blt g16m
    cmp r4, #14
    bgt g16m
    subs r0, r4, #1
    ldrb r0, [r3, r0]
g16m:
    lsrs r2, r0, #1
    orrs r2, r6
    lsrs r6, r6, #1
    orrs r2, r6
    bics r2, r0
    mov r6, r0
    movs r1, #0
    movs r5, #0
g16p:
    lsls r1, r1, #4
    mov r0, r6
    lsrs r0, r5
    push {r6}
    movs r6, #1
    tst r0, r6
    beq g16s
    adds r1, #INK
    b g16q
g16s:
    mov r0, r2
    lsrs r0, r5
    tst r0, r6
    beq g16q
    adds r1, #SHADOW
g16q:
    pop {r6}
    adds r5, #1
    cmp r5, #8
    bne g16p
    lsls r0, r4, #2
    str r1, [r7, r0]
    adds r4, #1
    cmp r4, #16
    bne g16r
    pop {r5}
    ldr r1, =FS
    cmp r5, r1
    bne g16e
    movs r4, #0x40
    ldr r5, =0x11111111
g16w:
    subs r4, #4
    ldr r0, [r7, r4]
    mov r1, r0
    ands r1, r5
    lsls r1, r1, #1
    lsrs r0, r0, #1
    ands r0, r5
    orrs r0, r1
    str r0, [r7, r4]
    bne g16w
g16e:
    mov r6, r7
    pop {r0, r2, r3, r4, r5, pc}
    .align 2
    .ltorg
'''


def check_thumb1(code, base):
    """ARM946E-S 는 썸-2 가 없다. bl 말고 32비트 명령이 섞이면 빌드를 멈춘다."""
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    end = 0
    for i in md.disasm(code, base):
        end = i.address + i.size
        if i.size != 2 and i.mnemonic not in ('bl',):
            if i.op_str == '' or not i.mnemonic.startswith(('.', 'vst', 'vld', 'stc', 'ldc', 'cdp', 'mcr', 'mrc', 'vrs')):
                print('주의 32비트:', hex(i.address), i.mnemonic, i.op_str)


def bl(src, dst):
    """Thumb bl 인코딩 (두 하프워드)."""
    off = dst - (src + 4)
    if not -0x400000 <= off < 0x400000:
        raise ValueError('bl 범위')
    off &= 0x7FFFFF
    return struct.pack('<HH', 0xF000 | (off >> 12), 0xF800 | ((off >> 1) & 0x7FF))


class Arm9:
    def __init__(self, data):
        self.d = bytearray(data)
        self.writes = []

    def put(self, addr, data, why, expect=None):
        o = addr - ARM9
        if expect is not None and bytes(self.d[o:o + len(expect)]) != expect:
            raise SystemExit(f'{addr:#x} 원본 불일치({why}): {self.d[o:o + len(expect)].hex()} != {expect.hex()}')
        for a, b, w in self.writes:
            if addr < b and a < addr + len(data):
                raise SystemExit(f'쓰기 겹침 {addr:#x} {why} / {w}')
        self.d[o:o + len(data)] = data
        self.writes.append((addr, addr + len(data), why))

    def get(self, addr, n):
        return bytes(self.d[addr - ARM9:addr - ARM9 + n])


def assemble(addr, syms):
    src = STUBS
    for k, v in sorted(syms.items(), key=lambda kv: -len(kv[0])):
        src = src.replace('#' + k, '#' + hex(v)).replace('=' + k, '=' + hex(v))
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB + keystone.KS_MODE_LITTLE_ENDIAN)
    # 키스톤은 ldr =상수 풀을 지원하지 않으므로 직접 만든다
    lines, pool = [], {}
    for ln in src.split('\n'):
        s = ln.strip()
        if s.startswith('ldr') and '=' in s:
            reg = s.split()[1].rstrip(',')
            val = s.split('=')[1]
            lab = pool.setdefault(int(val, 0), f'lit{len(pool)}')
            lines.append(f'    ldr {reg}, {lab}')
        elif s == '.ltorg' or s == '.align 2':
            continue
        else:
            lines.append(ln)
    body = '\n'.join(lines)
    # 풀은 끝에 둔다(ldr pc 상대 거리 1020 이내 확인은 어셈블러가 한다)
    tail = '\n'.join(f'{lab}:\n    .word {val:#x}' for val, lab in pool.items())
    labels = [ln.strip()[:-1] for ln in lines if ln.strip().endswith(':') and ' ' not in ln.strip()]
    enc, _ = ks.asm(body + '\n    nop\n    .balign 4\n' + tail, addr)
    code = bytes(enc)
    return code, labels


SITES_R4 = [(0x020437C4, 0x020437D8), (0x02043880, 0x02043894), (0x0204488C, 0x020448A0), (0x02044940, 0x02044954)]
SITES_R0 = [(0x02065016, 0x02065028), (0x02065092, 0x020650A4), (0x0209D836, 0x0209D842)]


def stub_sizes():
    return STUB[1] - STUB[0]


def install(a9, pack12, pack16, single, sub_style=None, lead0=0xDE, second=0xE4):
    """pack12/pack16: 2바이트 한글 글리프를 번호 순으로 이어 붙인 것."""
    n = len(pack12) // P12
    if len(pack16) // P16 != n:
        raise SystemExit('글리프 수 불일치')
    # 12×12: T1 → T2, 8×16: T2 나머지 → T3
    t1 = T1[0] + BUFSIZE
    n12a = (T1[1] - t1) // P12
    n12a = min(n12a, n)
    n12b = n - n12a
    t2 = T2[0]
    b_end = t2 + n12b * P12
    n16a = (T2[1] - b_end) // P16
    n16a = min(n16a, n)
    n16b = n - n16a
    if T3[0] + n16b * P16 > T3[1]:
        raise SystemExit(f'글리프 공간 부족: {T3[0] + n16b * P16 - T3[1]}바이트 넘침')
    a9.put(t1, pack12[:n12a * P12], '12×12 한글 앞')
    if n12b:
        a9.put(t2, pack12[n12a * P12:], '12×12 한글 뒤')
    a9.put(b_end, pack16[:n16a * P16], '8×16 한글 앞')
    if n16b:
        a9.put(T3[0], pack16[n16a * P16:], '8×16 한글 뒤')
    a9.put(BUF, bytes(BUFSIZE), '글리프 버퍼')
    syms = dict(LEAD0=lead0, SECOND=second, F12=F12, FS=FS, W1=W1, HANGUL_W=HANGUL_W, P12=P12, P16=P16,
                N12A=n12a, T12A=t1, T12B=t2 - n12a * P12, N16A=n16a, T16A=b_end,
                T16B=T3[0] - n16a * P16, BUF2=BUF + 0x60, BUF=BUF, INK=1, SHADOW=2,
                TBL=SPARE[0], SLOTS=112, VFONT=0x0620C000)
    code, labels = assemble(STUB[0], syms)
    if len(code) > STUB[1] - STUB[0]:
        raise SystemExit(f'스텁 공간 부족 {len(code)}')
    a9.put(STUB[0], code, '스텁')
    # 진입점은 스텁 맨 앞 점프표(하프워드 하나씩)
    addr = {k: STUB[0] + i * 2 for i, k in enumerate(('ko_dec_r4', 'ko_dec_r0', 'ko_g12', 'ko_gb', 'ko_g16', 'ko_tile'))}
    check_thumb1(code, STUB[0])
    # 리드 비교: cmp r1,#E4 / beq → cmp r1,#LEAD0 / bge
    for cmp_at, two in SITES_R4:
        a9.put(cmp_at, bytes([lead0, 0x29]), '리드 비교', bytes([0xE4, 0x29]))
        o = a9.get(cmp_at + 2, 2)
        if o[1] != 0xD0:
            raise SystemExit('beq 아님')
        a9.put(cmp_at + 2, bytes([o[0], 0xDA]), '리드 분기')
        a9.put(two, bl(two, addr['ko_dec_r4']), '2바이트 해독', bytes.fromhex('6178e431'))
    for cmp_at, two in SITES_R0:
        a9.put(cmp_at, bytes([lead0, 0x29]), '리드 비교', bytes([0xE4, 0x29]))
        o = a9.get(cmp_at + 2, 2)
        if o[1] != 0xD0:
            raise SystemExit('beq 아님')
        a9.put(cmp_at + 2, bytes([o[0], 0xDA]), '리드 분기')
        a9.put(two, bl(two, addr['ko_dec_r0']), '2바이트 해독', bytes.fromhex('4178e431'))
    # 타일 렌더러: 한글을 VRAM 동적 칸으로(폴더 편집 위 화면 칩 이름)
    a9.put(0x02012C8E, bl(0x02012C8E, addr['ko_tile']) + NOP * 3, '타일 렌더러', bytes.fromhex('e42902d1401c01785e31'))
    a9.put(SPARE[0], bytes(SPARE[1] - SPARE[0]), '동적 칸 표')
    # 12×12 그리기 두 곳: 글리프 주소·폭
    orig12 = bytes.fromhex('204c60274f433f191f4c89006458')
    a9.put(0x02065428, bl(0x02065428, addr['ko_g12']) + NOP * 5, '12×12 훅1', orig12)
    # 원본은 movs r4,#0xb / push {r4} 로 폭을 11 로 고정하고 그 값을 행 카운터로 쓴다.
    # 행 카운터는 0xb 로 두고 r4(폭)만 살린다: GBA 판 「폭+1행」 함정과 같은 구조.
    a9.put(0x02065436, bytes.fromhex('0b2001b4'), '행 수 고정, 폭 살림', bytes.fromhex('0b2410b4'))
    orig12b = bytes.fromhex('164c60274f433f19154c89006458')
    a9.put(0x020654D4, bl(0x020654D4, addr['ko_g12']) + NOP * 5, '12×12 훅2', orig12b)
    # 비례폭 그리기
    a9.put(0x0209D886, bl(0x0209D886, addr['ko_gb']) + NOP * 6, '비례폭 훅',
           bytes.fromhex('60274f433f18214cee78b600a4598900'))
    a9.put(0x0209D896, NOP, '비례폭 훅 끝', bytes.fromhex('6358'))
    # 8×16 칸 복사
    a9.put(0x020650CA, bl(0x020650CA, addr['ko_g16']), '8×16 훅', bytes.fromhex('8f01f619'))
    # 폭 표: 1바이트 한글
    for table in (W1, W2):
        for code_ in single:
            a9.put(table + code_ * 4, struct.pack('<I', HANGUL_W), '폭')
    return dict(n=n, n12a=n12a, n16a=n16a, stub=len(code),
                free=T3[1] - (T3[0] + n16b * P16) if n16b else T2[1] - (b_end + n * P16))
