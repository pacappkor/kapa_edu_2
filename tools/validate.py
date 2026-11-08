#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""구조 검증 + 처리 현황 문서(docs/STATUS.md) 생성 — 2차 시험.

사용법 (저장소 루트에서):  python tools/validate.py [--write-status]
검사: 과목·회차 폴더의 문제 번호 연속성(01.tex..NN.tex), 메타데이터 줄, longquestion 환경,
      배점 합계(100점 기준, 문제 첫 줄의 '(NN점)' 기준 — 참고용 경고), review 상태/flags/reviewflag 집계.
"""
import json, pathlib, re, sys, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {'latex', 'tools', 'build', 'docs', 'skills', 'sources', '.git', '.github'}

def markdown_tilde_errors():
    """Markdown 본문의 물결표(~)는 GitHub 에서 두 개가 한 줄에 있으면 취소선(~텍스트~)으로 렌더링된다.
    범위는 '–'(en dash)로 쓴다. 코드 스팬(`...`)과 코드 블록 안은 검사하지 않는다."""
    out = []
    for md in sorted(ROOT.rglob('*.md')):
        if {'.git', 'build'} & set(md.relative_to(ROOT).parts):
            continue
        fence = False
        for i, line in enumerate(md.read_text(encoding='utf-8').split('\n'), 1):
            if re.match(r'\s*(```|~~~)', line):
                fence = not fence; continue
            if fence:
                continue
            prose = re.sub(r'`+[^`]*`+', '', line)
            if '~' in prose:
                out.append(f'{md.relative_to(ROOT).as_posix()}:{i}: 범위 물결표 "~" 대신 "–" 를 쓴다(GitHub 취소선 방지)')
    return out

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    write = '--write-status' in sys.argv
    subjects = json.loads((ROOT / 'subjects.json').read_text(encoding='utf-8'))['subjects']
    errors, warns, table = [], [], []
    for sd in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP):
        for rd in sorted((d for d in sd.iterdir() if d.is_dir() and d.name.isdigit()), key=lambda d: int(d.name)):
            files = sorted(f for f in rd.glob('[0-9][0-9].tex') if f.stem != '00')
            nums = [int(f.stem) for f in files]
            if nums != list(range(1, len(nums) + 1)):
                errors.append(f'{sd.name}/{rd.name}: problem numbers not contiguous {nums}')
            st = collections.Counter(); flags = collections.Counter(); rflags = 0; pts = 0
            for f in files:
                t = f.read_text(encoding='utf-8')
                m = re.search(r'^%% kapa: (.*)$', t, re.M)
                if not m: errors.append(f'{f.relative_to(ROOT)}: missing %% kapa:'); continue
                meta = dict(x.split('=', 1) for x in m.group(1).split() if '=' in x)
                pts += int(meta.get('points', 0))
                if '%% source:' not in t: errors.append(f'{f.relative_to(ROOT)}: missing %% source:')
                if '\\begin{longquestion}' not in t: errors.append(f'{f.relative_to(ROOT)}: no longquestion env')
                cm = re.search(r'^%% conversion: .*?review=(\S+?);\s*flags=(.*)$', t, re.M)
                if cm:
                    st['pending' if cm.group(1) == 'pending' else 'proofread'] += 1
                    for fl in cm.group(2).split(','):
                        fl = fl.strip()
                        if fl and fl != 'none': flags[fl] += 1
                rflags += t.count('\\reviewflag{')
            if pts and pts != 100: warns.append(f'{sd.name}/{rd.name}: points sum {pts} (≠100, 메타데이터 확인)')
            table.append(dict(subject=sd.name, round=int(rd.name), problems=len(files), points=pts, pending=st['pending'],
                              proofread=st['proofread'], flags=dict(flags), reviewflags=rflags,
                              instructions=(rd / '00.tex').exists()))
    errors += markdown_tilde_errors()
    print(f'errors: {len(errors)}  warnings: {len(warns)}')
    for e in errors: print('ERROR', e)
    for w in warns: print('WARN ', w)
    if write:
        ko = {s['folder']: s['name_ko'] for s in subjects}
        L = ['# 처리 현황 (자동 생성: `python tools/validate.py --write-status`)', '',
             '| 과목 | 회차 | 문제 수 | 배점 합계 | 교정 완료 | 자동 변환(미교정) | reviewflag | 주요 flags |', '|---|---|---|---|---|---|---|---|']
        for r in table:
            top = ', '.join(f'{k}×{v}' for k, v in sorted(r['flags'].items(), key=lambda x: -x[1])[:4])
            L.append(f"| {ko.get(r['subject'], r['subject'])} | {r['round']} | {r['problems']} | {r['points'] or '-'} | {r['proofread']} | {r['pending']} | {r['reviewflags']} | {top or '-'} |")
        L += ['', f"합계: 문제 파일 {sum(r['problems'] for r in table)}개, 교정 완료 {sum(r['proofread'] for r in table)}개, "
              f"자동 변환(미교정) {sum(r['pending'] for r in table)}개", '', 'flags 의미는 AGENTS.md 의 "flags 사전" 참고.']
        (ROOT / 'docs').mkdir(exist_ok=True)
        (ROOT / 'docs' / 'STATUS.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
        (ROOT / 'docs' / 'status.json').write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding='utf-8')
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
