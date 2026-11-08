#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""figures/ 의 PNG 용량 최적화 (무손실에 가깝게: 회색조·팔레트 변환 + 최대 압축).

사용법 (저장소 루트에서):  python tools/optimize_figures.py [--check]
- 색이 거의 없는 그림은 8bit 회색조(L), 256색 이하면 팔레트(P), 그 밖은 RGB 최적 압축.
- 최적화 결과가 원본보다 크면 원본 유지. 해상도(픽셀 수)는 바꾸지 않는다.
- 그림은 가능하면 TikZ/pgfplots 로 문항 파일 안에 재현하는 것이 원칙이며(AGENTS.md), 이 스크립트는
  사진·지적도처럼 PNG 로 남겨야 하는 그림에만 해당한다.
"""
import io, pathlib, sys
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent

def optimise(p):
    im = Image.open(p); im.load()
    rgb = im.convert('RGB')
    cands = []
    # grayscale if channels are (nearly) equal
    r, g, b = rgb.split()
    from PIL import ImageChops
    diff = max(ImageChops.difference(r, g).getextrema()[1], ImageChops.difference(g, b).getextrema()[1])
    if diff <= 8:
        cands.append(rgb.convert('L'))
    colors = rgb.getcolors(256)
    if colors is not None:
        cands.append(rgb.quantize(colors=len(colors), method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    cands.append(rgb)
    best = None
    for c in cands:
        buf = io.BytesIO(); c.save(buf, 'PNG', optimize=True)
        if best is None or buf.tell() < len(best): best = buf.getvalue()
    return best

def main():
    check = '--check' in sys.argv
    before = after = 0
    for p in sorted(ROOT.glob('*/*/figures/*.png')):
        old = p.stat().st_size; new = optimise(p)
        before += old
        if len(new) < old:
            after += len(new)
            if not check: p.write_bytes(new)
        else:
            after += old
    print(f'PNG total {before/1024:.0f} KB -> {after/1024:.0f} KB' + (' (check only)' if check else ''))

if __name__ == '__main__':
    main()
