#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate round/period PDFs and MkDocs sources in build/ (no network).

Run from any directory: python -I -B tools/site.py
Content compilation failures are displayed, never silently published as PDFs.
Missing tools/packages and invalid metadata stop generation instead.
"""
import csv
import html
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('exam_build', ROOT / 'tools/build.py')
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)
OUT = ROOT / 'build'
DOCS = OUT / 'site-src'
QNET = 'https://www.q-net.or.kr/cst003.do?id=cst00309&gSite=L&gId=60'


def attribution(round_no):
    source = f'출처: 한국산업인력공단, [Q-Net 감정평가사 기출문제]({QNET}).'
    if 25 <= round_no <= 37:
        return source + ' 공지 artlSeq=5259147(2014년 자료부터)에 따른 **공공누리 제1유형(출처표시)** 대상입니다.'
    if 19 <= round_no <= 24:
        return source + ' 공식 공개 자료이며, 이 저장소는 별도 이용허락이나 공공누리 적용을 주장하지 않습니다. 이용·재배포 시 권리와 이용 조건을 별도로 확인하세요.'
    raise ValueError(f'NOTICE.md attribution policy not defined for round {round_no}')


def discover(root=ROOT):
    """Only canonical NN.tex fragments in subjects.json; metadata defines periods."""
    subjects = json.loads((root / 'subjects.json').read_text(encoding='utf-8'))
    records = []
    for subject in subjects['subjects']:
        for path in sorted((root / subject['folder']).glob('[0-9]*/[0-9][0-9].tex')):
            line = path.read_text(encoding='utf-8').splitlines()[0]
            meta = dict(re.findall(r'(\w+)=([^\s]+)', line))
            required = ('round', 'period', 'seq', 'exam', 'subject')
            if not line.startswith('%% kapa:') or any(k not in meta for k in required):
                raise ValueError(f'Invalid metadata: {path.relative_to(root)}')
            rd, period, seq = (int(meta[k]) for k in ('round', 'period', 'seq'))
            attribution(rd)  # Unknown future rounds require explicit notice review.
            if str(rd) != path.parent.name or meta['subject'] != subject['folder']:
                raise ValueError(f'Metadata/path mismatch: {path.relative_to(root)}')
            records.append(dict(path=path, round=rd, period=period, seq=seq,
                                subject=subject['name_ko'], number=int(meta.get('number', '0')),
                                subject_order=subjects['subjects'].index(subject),
                                exam=int(meta['exam']), form=meta.get('form', '')))
    if not records:
        raise ValueError('No question fragments found')
    if len({r['exam'] for r in records}) != 1:
        raise ValueError('Mixed exam metadata')
    return sorted(records, key=lambda r: (r['round'], r['period'], r['subject_order'], r['seq']))


def wrapper(records):
    """Reuse build.py's package/options; keep wrappers in build/ for subimport."""
    preamble = build.wrapper(records[0]['path'].parent, True).split('\\section*', 1)[0]
    parts = [preamble]
    previous = None
    for rec in records:
        section = (rec['period'], rec['subject'])
        if section != previous:
            if previous is not None:
                parts.append('\\clearpage\n')
            parts.append(f"\\section*{{제{rec['round']}회 — {rec['period']}교시 — {rec['subject']}}}\n")
            previous = section
        rel = rec['path'].relative_to(ROOT)
        parts.append('\\subimport{../%s/}{%s}\n' % (rel.parent.as_posix(), rel.name))
    return ''.join(parts) + '\\end{document}\n'


def clean_error(text):
    # Public reports never expose the local checkout path.
    return text.replace(str(ROOT), '.').replace(ROOT.as_posix(), '.')


def compile_document(name, records):
    tex = OUT / (name + '.tex')
    pdf = tex.with_suffix('.pdf')
    pdf.unlink(missing_ok=True)
    tex.write_text(wrapper(records), encoding='utf-8')
    ok, errors, missing = build.compile_tex(tex, OUT)
    result = dict(name=name, ok=ok, errors=[clean_error(e) for e in errors], missing_glyphs=missing)
    if ok and pdf.exists():
        shutil.copy2(pdf, DOCS / 'pdf' / pdf.name)
    else:
        result['ok'] = False
        if not result['errors']:
            result['errors'] = ['XeLaTeX failed; inspect the local build log.']
    return result


def footer(repo, exam, rounds):
    lines = ['---', '자동 변환 및 교정한 자료입니다. 반드시 Q-Net 원본과 대조하세요. 사람의 표본 검수는 아직입니다.']
    if exam == 2:
        lines.append('**공식 모범답안 없음**. 이 사이트는 공식 답안을 제공하지 않습니다.')
    lines += [f'[오류 제보/질문: Discussions](https://github.com/pacappkor/{repo}/discussions) · '
              f'[확인된 오류: correction 이슈](https://github.com/pacappkor/{repo}/issues/new?template=correction.md)',
              f'[이용 조건 전문](https://github.com/pacappkor/{repo}/blob/main/NOTICE.md) · '
              f'[원본 출처 목록](https://github.com/pacappkor/{repo}/blob/main/docs/SOURCES.md)',
              '저장소 고유 변환·조판 코드와 문서: GPL-3.0-only. 원자료의 권리는 바뀌지 않습니다.']
    for rd in rounds:
        lines.append(f'제{rd}회({rd + 1989}): ' + attribution(rd))
    return '\n\n'.join(lines) + '\n'


def cell(value):
    return html.escape(value).replace('|', '&#124;').replace('\n', '<br>')


def answer_table(round_no, root=ROOT):
    path = root / 'answers/answers.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = [row for row in csv.DictReader(stream) if int(row['round']) == round_no]
    if not rows:
        raise ValueError(f'Missing answer rows: {round_no}')
    lines = ['## 최종 정답', '출처: 한국산업인력공단, [Q-Net 최종 정답](https://www.q-net.or.kr/cst003.do?id=cst00310&gSite=L&gId=60). '
             'answers/answers.csv 전사이며 원본 최종 정답표를 확인하세요.',
             '| 교시 | 형 | 과목 | 번호 | 정답 | 비고 |', '|---|---|---|---|---|---|']
    for row in rows:
        lines.append('| ' + ' | '.join(cell(row[k]) for k in ('period', 'form', 'subject', 'number', 'answer', 'note')) + ' |')
    return '\n\n'.join(lines[:2]) + '\n\n' + '\n'.join(lines[2:])


def result_link(result):
    if result['ok']:
        text = f"[PDF 내려받기](pdf/{result['name']}.pdf)"
    else:
        text = '**PDF 조판 실패 — 불완전한 PDF는 게시하지 않습니다.**\n\n' + '\n\n'.join(
            html.escape(e) for e in result['errors'])
    if result['missing_glyphs']:
        text += '\n\n**주의: 글꼴 누락** ' + cell(' '.join(result['missing_glyphs'])) + ' — 원본과 대조하세요.'
    return text


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    start = time.perf_counter()
    records = discover()
    exam = records[0]['exam']
    repo = f'kapa_edu_{exam}'
    if not shutil.which('xelatex') or not build.preflight():
        return 2
    build.load_subjects()
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / 'pdf').mkdir(parents=True)
    rounds = sorted({r['round'] for r in records})
    results, failures = [], []
    periods = 0
    for rd in rounds:
        selected = [r for r in records if r['round'] == rd]
        whole = compile_document(f'round-{rd}', selected)
        results.append(whole)
        page = [f'# 제{rd}회({rd + 1989}) — {exam}차', '## 전체 회차', result_link(whole)]
        for period in sorted({r['period'] for r in selected}):
            subset = [r for r in selected if r['period'] == period]
            periods += 1
            result = compile_document(f'round-{rd}-period-{period}', subset)
            results.append(result)
            page += [f'## {period}교시', ', '.join(dict.fromkeys(r['subject'] for r in subset)), result_link(result)]
            if not result['ok']:
                page.append('### 개별 문항 진단')
                for rec in subset:
                    rel = rec['path'].relative_to(ROOT).as_posix()
                    single = compile_document('diagnostic-' + rel.replace('/', '-').removesuffix('.tex'), [rec])
                    # Diagnostic PDFs are not site deliverables.
                    (DOCS / 'pdf' / (single['name'] + '.pdf')).unlink(missing_ok=True)
                    if not single['ok']:
                        failure = dict(snippet=rel, errors=single['errors'])
                        failures.append(failure)
                        page.append(f"- `{rel}`: " + cell('; '.join(single['errors'])))
                if not any(f['snippet'] in {r['path'].relative_to(ROOT).as_posix() for r in subset} for f in failures):
                    page.append('개별 문항은 통과했으나 묶음 조판이 실패했습니다. 위 묶음 오류를 확인하세요.')
        if exam == 1:
            page.append(answer_table(rd))
        page.append(footer(repo, exam, [rd]))
        (DOCS / f'round-{rd}.md').write_text('\n\n'.join(page), encoding='utf-8')
        print(f'Round {rd}: complete', flush=True)
    home = [f'# 감정평가사 {exam}차 기출문제',
            '공식 사이트가 아닌 기출문제 LaTeX 변환 자료 모음입니다. PDF는 정답을 숨긴 학습용 조판입니다.',
            f'{len(rounds)}개 회차 · {periods}개 교시 · {len(records)}개 문항 파일',
            *[f'- [제{rd}회({rd + 1989})](round-{rd}.md)' for rd in reversed(rounds)],
            footer(repo, exam, rounds)]
    (DOCS / 'index.md').write_text('\n\n'.join(home), encoding='utf-8')
    report = dict(rounds=len(rounds), periods=periods, snippets=len(records),
                  elapsed_seconds=round(time.perf_counter() - start, 3),
                  pdf_bytes=sum(p.stat().st_size for p in (DOCS / 'pdf').glob('*.pdf')),
                  documents=results, snippet_failures=failures)
    (OUT / 'site-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('documents', 'snippet_failures')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
