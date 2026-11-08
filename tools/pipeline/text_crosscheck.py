#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""문항 파일의 한글 낱말이 원본 텍스트에 실제로 있는지 대조 (원문 변경·오탈자 '교정' 탐지용).

usage: python -I text_crosscheck.py <저장소> <원본텍스트폴더> [회차...]
  <원본텍스트폴더>/<회차>_<p1|p2>.txt  — 원본 텍스트(텍스트 PDF 는 PyMuPDF get_text, HWP 는 rhwp export-text 를 이어 붙인 것)
출력: 원본(띄어쓰기 제거)에 없는 한글 낱말 목록을 파일별로. OCR 회차(제32~34회)는 원본 텍스트가 없어 대상 아님.
- LaTeX 명령·수식·주석·메타데이터 줄은 제외하고, 한글이 포함된 2글자 이상 토큰만 검사한다.
- 결과는 '의심 목록'이다. 줄바꿈·하이픈·특수문자 차이로 인한 오탐이 있을 수 있으므로 원본 이미지로 최종 확인한다.
"""
import json, pathlib, re, sys

def norm(s):
    s = s.replace('ㆍ', '·').replace('･', '·').replace('․', '·').replace('｢', '「').replace('｣', '」')
    return re.sub(r'\s+', '', s)

def tex_tokens(t):
    lines = [l for l in t.split('\n') if not l.startswith('%%')]
    t = '\n'.join(re.sub(r'(?<!\\)%.*', '', l) for l in lines)
    t = re.sub(r'\$\$.*?\$\$|\$[^$]*\$', ' ', t, flags=re.S)
    t = t.split('\\end{question}')[0] if '\\end{question}' in t else t
    t = re.sub(r'\\(?:text|textbf|uline|underline|emph|textit|mathrm|makebox|parbox)\s*(?:\[[^\]]*\])?\s*\{', ' ', t)
    t = re.sub(r'\\[A-Za-z]+\*?', ' ', t)
    t = re.sub(r'[{}\[\]&\\~^_]', ' ', t)
    # compare maximal runs of Hangul syllables only: PDF text layers often order digits/latin/punctuation
    # differently from the visual line, so only Hangul runs are reliable for this check
    return [x for x in re.findall(r'[가-힣]+', t) if len(x) >= 2]

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    repo, srcdir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    rounds = set(sys.argv[3:])
    report = {}
    for f in sorted(repo.glob('*/*/[0-9][0-9].tex')):
        rnd = f.parts[-2]
        if rounds and rnd not in rounds: continue
        t = f.read_text(encoding='utf-8')
        m = re.search(r'period=(\d)', t)
        if not m: continue
        src = srcdir / f'{rnd}_p{m.group(1)}.txt'
        if not src.exists(): continue
        S = ''.join(re.findall(r'[가-힣]+', src.read_text(encoding='utf-8', errors='replace')))
        miss = sorted({tok for tok in tex_tokens(t) if norm(tok) not in S})
        if miss:
            report[f.relative_to(repo).as_posix()] = miss
    for k, v in report.items():
        print(k, '|', ' '.join(v))
    print(f'# files with unmatched tokens: {len(report)}', file=sys.stderr)

if __name__ == '__main__':
    main()
