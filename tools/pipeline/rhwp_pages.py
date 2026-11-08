#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""HWP 원본을 rhwp 로 PDF 렌더링한 뒤 페이지 PNG 로 저장 (원본 대조 교정용).

usage: python -I rhwp_pages.py <rhwp.exe 경로> <원본.hwp> <출력 폴더> [dpi]

- rhwp: https://github.com/edwardkim/rhwp (MIT). Releases 의 플랫폼 바이너리를 받고 SHA256SUMS.txt 로 검증해 사용.
  검증한 버전: v0.8.7 (`rhwp export-pdf`).
- 렌더링은 글꼴 차이로 쪽 나눔·단 배치가 원본과 다를 수 있고 꼬리말이 본문 끝 줄과 겹치기도 한다.
  내용(본문·표·수식·보기 상자·그림)은 원본 그대로이므로 '내용 대조'용으로만 쓴다.
- 텍스트·수식 추출은 kordoc 결과(수식 LaTeX)를 기본으로 하고, rhwp `export-tables`/`export-markdown` 은
  표 형태 선택지 구조 확인 등 보조 근거로 사용한다.
"""
import pathlib, subprocess, sys
import pymupdf

def main():
    rh, src, out = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 130
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / (src.stem + '.rhwp.pdf')
    subprocess.run([rh, 'export-pdf', str(src), '-o', str(pdf)], check=True)
    doc = pymupdf.open(pdf)
    for i, pg in enumerate(doc):
        pg.get_pixmap(dpi=dpi).save(out / f'page-{i + 1:02d}.png')
    print(f'{src.name}: {len(doc)} pages -> {out}')

if __name__ == '__main__':
    main()
