#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""회차·과목별 묶음 PDF 빌드 / 컴파일 검증.

사용법 (저장소 루트에서):
  python tools/build.py                      # 전체 과목·회차 컴파일
  python tools/build.py civil_law            # 특정 과목 전체
  python tools/build.py civil_law/37         # 특정 과목·회차
  python tools/build.py --noanswers ...      # 정답 숨김
  python tools/build.py --single civil_law/37/01.tex   # 문항 1개만 단독 컴파일

동작: build/<subject>_<round>.tex 래퍼를 생성해 각 문항 파일을 \\subimport 로 포함하고
XeLaTeX 로 컴파일한다. 결과 PDF 와 로그는 build/ 에 남는다(.gitignore 대상).
종료 코드: 실패한 문서가 하나라도 있으면 1.
"""
import argparse, pathlib, re, subprocess, sys, json, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
SUBJECT_KO = {}

def load_subjects():
    f = ROOT / 'subjects.json'
    if f.exists():
        for s in json.loads(f.read_text(encoding='utf-8'))['subjects']:
            SUBJECT_KO[s['folder']] = s['name_ko']

def question_dirs(targets):
    dirs = []
    for sub in sorted(p for p in ROOT.iterdir() if p.is_dir() and (ROOT / p.name).joinpath().exists()):
        if sub.name.startswith(('.', '_')) or sub.name in ('latex', 'tools', 'build', 'docs', 'skills', 'sources', 'answers'):
            continue
        for rd in sorted((d for d in sub.iterdir() if d.is_dir() and d.name.isdigit()), key=lambda d: int(d.name)):
            key = f'{sub.name}/{rd.name}'
            if not targets or any(key == t or sub.name == t for t in targets):
                dirs.append(rd)
    return dirs

def wrapper(rd, noanswers):
    rel = rd.relative_to(ROOT).as_posix()
    files = sorted(rd.glob('[0-9][0-9].tex'))
    opt = '[noanswers]' if noanswers else ''
    name = SUBJECT_KO.get(rd.parent.name, rd.parent.name)
    body = []
    for f in files:
        body.append('\\subimport{../%s/}{%s}' % (rel, f.name))
    return ('\\documentclass[10pt,a4paper]{article}\n'
            '\\usepackage[margin=18mm]{geometry}\n'
            '\\usepackage%s{kapa-exam}\n'
            '\\begin{document}\n'
            '\\section*{제%s회 감정평가사 시험 — %s}\n'
            '%s\n\\end{document}\n') % (opt, rd.name, name, '\n'.join(body))

def compile_tex(tex, cwd):
    env = dict(**__import__('os').environ)
    sep = ';' if sys.platform.startswith('win') else ':'
    # "." first, then latex/, then trailing separator = TeX default search path
    env['TEXINPUTS'] = sep.join(['.', str(ROOT / 'latex'), env.get('TEXINPUTS', '')])
    cmd = ['xelatex', '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', tex.name]
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    log = (cwd / tex.with_suffix('.log').name)
    logtxt = log.read_text(encoding='utf-8', errors='replace') if log.exists() else r.stdout
    errs = re.findall(r'^.*?:\d+: .*$|^! .*$', logtxt, re.M)
    missing = sorted(set(re.findall(r'Missing character: There is no (.) ', logtxt)))
    return r.returncode == 0, errs[:10], missing

def preflight():
    """컴파일 전에 TeX Live 의 한글 패키지·글꼴과 저장소 경로를 확인한다."""
    if not str(ROOT).isascii() or ' ' in str(ROOT):
        print(f'경고: 저장소 경로에 비 ASCII 문자 또는 공백이 있습니다: {ROOT}\n'
              'KTUG Windows 안내는 한글·공백 없는 폴더·파일명을 권장합니다. '
              '프로그램에 따라 TeX Live 오류가 날 수 있습니다. '
              'README.md 의 "개발 환경 (한글 LaTeX)" 절을 확인하세요.\n'
              'https://www.ktug.org/getting-started/windows-texlive/', file=sys.stderr)
    guide = 'README.md 의 "개발 환경 (한글 LaTeX)" 절을 확인하세요.'
    kpsewhich = shutil.which('kpsewhich')
    if kpsewhich is None:
        print(f'사전 검사 실패: PATH 에 kpsewhich 가 없습니다. TeX Live 설치·PATH 와 {guide}', file=sys.stderr)
        return False
    missing = []
    for name in ('UnBatang.ttf', 'UnDotum.ttf', 'kotex.sty'):
        try:
            result = subprocess.run([kpsewhich, name], capture_output=True, text=True,
                                    encoding='utf-8', errors='replace', timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'사전 검사 실패: kpsewhich {name} 실행 오류: {exc}. {guide}', file=sys.stderr)
            return False
        if result.returncode != 0 or not result.stdout.strip():
            missing.append(name)
    if missing:
        print(f'사전 검사 실패: TeX Live 에서 {", ".join(missing)} 을 찾지 못했습니다. '
              f'kotex·unfonts-core 설치를 확인하세요(글꼴: tlmgr install unfonts-core). {guide}', file=sys.stderr)
        return False
    print('사전 검사 통과: UnBatang.ttf, UnDotum.ttf, kotex.sty')
    return True


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument('targets', nargs='*')
    ap.add_argument('--noanswers', action='store_true')
    ap.add_argument('--single')
    ap.add_argument('--skip-preflight', action='store_true', help='한글 LaTeX 사전 검사 생략')
    a = ap.parse_args()
    if shutil.which('xelatex') is None:
        print('xelatex not found on PATH', file=sys.stderr); return 2
    if not a.skip_preflight and not preflight():
        return 2
    load_subjects()
    BUILD.mkdir(exist_ok=True)
    report = []
    if a.single:
        f = (ROOT / a.single).resolve()
        rd = f.parent
        tex = BUILD / ('single_' + '_'.join(f.relative_to(ROOT).with_suffix('').parts) + '.tex')
        tex.write_text(wrapper(rd, a.noanswers).split('\\subimport')[0].rstrip()
                       .replace('\\section*', '%') + '\n\\subimport{../%s/}{%s}\n\\end{document}\n' % (rd.relative_to(ROOT).as_posix(), f.name), encoding='utf-8')
        ok, errs, miss = compile_tex(tex, BUILD)
        print('OK' if ok else 'FAIL', a.single, *errs, sep='\n')
        return 0 if ok else 1
    fails = 0
    for rd in question_dirs(a.targets):
        tex = BUILD / f'{rd.parent.name}_{rd.name}.tex'
        tex.write_text(wrapper(rd, a.noanswers), encoding='utf-8')
        ok, errs, miss = compile_tex(tex, BUILD)
        fails += not ok
        report.append({'doc': f'{rd.parent.name}/{rd.name}', 'ok': ok, 'errors': errs, 'missing_glyphs': miss})
        print(('OK  ' if ok else 'FAIL'), f'{rd.parent.name}/{rd.name}', ('missing glyphs: ' + ''.join(miss)) if miss else '', *(errs[:3] if not ok else []))
    (BUILD / 'build_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(report) - fails}/{len(report)} documents compiled')
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
