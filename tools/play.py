#!/usr/bin/env python3
"""길찾기용 입력 재생. 사용법: play.py 롬 상태 이름 토큰들(쉼표)
토큰: U40/D40/LE40/RI40 = 그 방향 40프레임 누름, UL30 등 동시 입력(U+LE, U+RI, D+LE, D+RI 는 UL/UR/DL/DR),
A B X Y L R ST SE = 한 번 누름, wN 대기, S 캡처, Tx:y 터치, AN = A 를 N 번(60프레임 간격).
"""
import os
import re
import sys

sys.path.insert(0, 'tools')
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import emutest  # noqa: E402
from desmume.controls import keymask  # noqa: E402

K = emutest.KEYS
HOLD = {'U': ['U'], 'D': ['D'], 'LE': ['LE'], 'RI': ['RI'], 'UL': ['U', 'LE'], 'UR': ['U', 'RI'],
        'DL': ['D', 'LE'], 'DR': ['D', 'RI']}


def main():
    rom, st, name, seq = sys.argv[1:5]
    emu = emutest.Emu(rom, None if st == '-' else st)
    for t in seq.split(','):
        m = re.fullmatch(r'(UL|UR|DL|DR|U|D|LE|RI)(\d+)', t)
        if m:
            keys = HOLD[m.group(1)]
            for k in keys:
                emu.e.input.keypad_add_key(keymask(K[k]))
            emu.run(int(m.group(2)))
            for k in keys:
                emu.e.input.keypad_rm_key(keymask(K[k]))
            emu.run(10)
        elif t.startswith('w'):
            emu.run(int(t[1:]))
        elif t == 'S':
            emu.shot(f'{name}{len(emu.shots):02d}')
        elif t[0] == 'T':
            x, y = map(int, t[1:].split(':'))
            emu.e.input.touch_set_pos(x, y)
            emu.run(8)
            emu.e.input.touch_release()
            emu.run(40)
        elif re.fullmatch(r'A\d+', t):
            for _ in range(int(t[1:])):
                emu.press(K['A'], after=60)
        else:
            emu.press(K[t], after=50)
    emu.shot(f'{name}{len(emu.shots):02d}')
    emu.save(f'{name}_end')
    emu.grid(name, cols=8, scale=0.5)
    emutest.shutdown()


if __name__ == '__main__':
    main()
