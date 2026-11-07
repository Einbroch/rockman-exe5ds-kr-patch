#!/usr/bin/env python3
"""NDS 롬을 풀어 분석용 파일을 만든다.

사용법: python tools/unpack.py <롬.nds> <출력 폴더>
결과: 출력/fs/... (파일시스템), arm9.bin(압축 해제), overlay/NNNN.bin(압축 해제), filelist.tsv
"""
import pathlib
import sys

import ndspy.codeCompression
import ndspy.rom


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    (out / 'overlay').mkdir(parents=True, exist_ok=True)
    rows = []
    for i, data in enumerate(rom.files):
        name = rom.filenames.filenameOf(i)
        if name is None:
            continue
        p = out / 'fs' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        rows.append(f'{name}\t{len(data)}\t{bytes(data[:4]).hex()}')
    (out / 'filelist.tsv').write_text('\n'.join(rows) + '\n', encoding='utf-8')
    (out / 'arm9.bin').write_bytes(rom.loadArm9().save(compress=False))
    for n, ov in rom.loadArm9Overlays().items():
        (out / 'overlay' / f'{n:04d}.bin').write_bytes(ov.data)
    print(f'{out}: 파일 {len(rows)}개, 오버레이 {len(rom.arm9OverlayTable) // 32}개')


if __name__ == '__main__':
    main()
