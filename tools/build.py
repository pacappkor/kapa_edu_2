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

# 글꼴과 kotex 는 고정하고 직접 패키지 의존성은 스타일에서 읽는다.
PREFLIGHT_FILES = ('UnBatang.ttf', 'UnDotum.ttf', 'batang.ttf', 'lmroman10-regular.otf', 'kotex.sty')


# TeX Live 2026 의 kpsewhich 경로로 확인한 파일별 제공 패키지.
TEXLIVE_PACKAGES = {
    'UnBatang.ttf': 'unfonts-core', 'UnDotum.ttf': 'unfonts-core',
    'batang.ttf': 'baekmuk', 'lmroman10-regular.otf': 'lm', 'kotex.sty': 'kotex-utf',
    'iftex.sty': 'iftex', 'fontspec.sty': 'fontspec',
    'newunicodechar.sty': 'newunicodechar', 'amsmath.sty': 'amsmath',
    'amssymb.sty': 'amsfonts', 'graphicx.sty': 'graphics', 'import.sty': 'import',
    'array.sty': 'tools', 'tabularx.sty': 'tools', 'multirow.sty': 'multirow',
    'makecell.sty': 'makecell', 'longtable.sty': 'tools', 'booktabs.sty': 'booktabs',
    'enumitem.sty': 'enumitem', 'tikz.sty': 'pgf', 'pgfplots.sty': 'pgfplots',
    'xcolor.sty': 'xcolor', 'tcolorbox.sty': 'tcolorbox', 'ulem.sty': 'ulem',
    'needspace.sty': 'needspace',
}


def _tex_tokens(style):
    """스타일의 기본 catcode 기준: 제어 단어·제어 기호를 먼저 소비하고 주석을 버린다."""
    i = 0
    while i < len(style):
        start = i
        char = style[i]
        i += 1
        if char == '\\':
            if i < len(style) and (style[i].isascii() and style[i].isalpha() or style[i] == '@'):
                while i < len(style) and (style[i].isascii() and style[i].isalpha() or style[i] == '@'):
                    i += 1
            elif i < len(style):
                i += 1
        elif char == '%':
            while i < len(style) and style[i] != '\n':
                i += 1
            # 주석 끝의 줄바꿈도 TeX 에서는 토큰이 아니다.
            i += i < len(style)
            continue
        yield style[start:i]


def _group_end(tokens, start, closing):
    """이스케이프된 중괄호는 제어 기호이므로 깊이에 영향을 주지 않는다."""
    depth = 0
    for i in range(start + 1, len(tokens)):
        token = tokens[i]
        if token == closing and depth == 0:
            return i
        depth += {'{': 1, '}': -1}.get(token, 0)
    return None


def _package_groups(style):
    """매크로 확장 없이 실제 패키지 명령의 옵션과 중괄호 인자를 토큰 단위로 읽는다."""
    tokens = list(_tex_tokens(style))
    groups = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        i += 1
        if token not in ('\\RequirePackage', '\\RequirePackageWithOptions', '\\usepackage', '\\string', '\\noexpand', '\\detokenize'):
            continue
        while i < len(tokens) and tokens[i].isspace():
            i += 1
        if token in ('\\string', '\\noexpand', '\\detokenize'):
            # 표시용 명령은 다음 토큰을 실행하지 않는다. detokenize 의 그룹도 건너뛴다.
            if token == '\\detokenize' and i < len(tokens) and tokens[i] == '{':
                end = _group_end(tokens, i, '}')
                i = len(tokens) if end is None else end + 1
            else:
                i += 1
            continue
        if i < len(tokens) and tokens[i] == '[':
            end = _group_end(tokens, i, ']')
            if end is None:
                break
            i = end + 1
            while i < len(tokens) and tokens[i].isspace():
                i += 1
        if i < len(tokens) and tokens[i] == '{':
            end = _group_end(tokens, i, '}')
            if end is None:
                break
            groups.append(''.join(tokens[i + 1:end]))
            i = end + 1
    return groups


def preflight_files():
    """스타일의 RequirePackage/RequirePackageWithOptions/usepackage 옵션·쉼표 목록을 포함한 검사 대상."""
    style = (ROOT / 'latex' / 'kapa-exam.sty').read_text(encoding='utf-8')
    groups = _package_groups(style)
    packages = (name.strip() + '.sty' for group in groups for name in group.split(',') if name.strip())
    return tuple(dict.fromkeys((*PREFLIGHT_FILES, *packages)))


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
    try:
        targets = preflight_files()
        def probe(names):
            return subprocess.run([kpsewhich, *names], capture_output=True, text=True,
                                  encoding='utf-8', errors='replace', timeout=10)

        result = probe(targets)
        # kpsewhich 는 누락된 이름의 빈 줄을 출력하지 않으므로 파일명으로 대조한다.
        found = {line.strip().replace('\\', '/').rsplit('/', 1)[-1]
                 for line in result.stdout.splitlines() if line.strip()}
        missing = []
        # 다중 이름을 지원하지 않거나 일부 결과만 반환하는 환경에서도 확인한다.
        # 정상 설치에서는 한 번의 프로세스 호출만 필요하다.
        for name in targets:
            if name not in found:
                result = probe((name,))
                if result.returncode != 0 or not result.stdout.strip():
                    missing.append(name)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f'사전 검사 실패: 스타일 읽기 또는 kpsewhich 실행 오류: {exc}. {guide}', file=sys.stderr)
        return False
    if missing:
        remedies = '; '.join(f'{name} → tlmgr install {TEXLIVE_PACKAGES[name]}' if name in TEXLIVE_PACKAGES
                             else f'{name} → tlmgr search --global --file /{name}'
                             if re.fullmatch(r'[A-Za-z0-9._-]+', name)
                             else f'{name!r} → 이 파일 이름으로 tlmgr search --global --file 을 사용해 제공 패키지를 찾으세요'
                             for name in missing)
        print(f'사전 검사 실패: TeX Live 에서 {", ".join(missing)} 을 찾지 못했습니다. '
              f'{remedies}. 다른 패키지도 누락되면 전체 설치(full scheme, tlmgr install scheme-full)를 권장합니다. '
              f'{guide}', file=sys.stderr)
        return False
    print(f'사전 검사 통과: {len(targets)}개 파일 확인: ' + ', '.join(targets))
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
