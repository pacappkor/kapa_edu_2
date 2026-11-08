# SPDX-License-Identifier: GPL-3.0-only
"""Generate 2차 problem .tex files from kordoc markdown.
usage: gen2.py <qnet_dir> <repo_dir> <round> <period 1|2|3> <md_file> [pages_note]
"""
import sys, re, json, pathlib, html
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from mdtex import inline, parse_html_table, parse_gfm_table, grid_table_to_latex
from PIL import Image

BS = chr(92)
SUBJ = {1: ('appraisal_practice', '감정평가실무'), 2: ('appraisal_theory', '감정평가이론'), 3: ('compensation_law', '감정평가 및 보상법규')}
Q = pathlib.Path(sys.argv[1]); REPO = pathlib.Path(sys.argv[2]); RND = int(sys.argv[3]); PER = int(sys.argv[4])
MD = pathlib.Path(sys.argv[5]); CONV = MD.parent
YEAR = RND + 1989
man = json.loads((Q / 'meta/manifest.json').read_text(encoding='utf-8'))
src = next((m for m in man if m['exam'] == 2 and m['round'] == RND and m['part'] in (f'p{PER}', 'all')), None)

MARK = re.compile(r'【\s*문(?:\s*제)?\s*(\d)\s*(?:】|1(?=\s)|\])?|^\[\s*문제\s*(\d+)\s*\]|^문제\s*(\d+)\s*[\.\)]?\s')
FOOTER = [re.compile(p) for p in (
    r'^\d+\s*-\s*\d+\s*-?\s*\[\s*\d\s*교시\s*\]\s*$', r'^-?\s*\d+\s*-\s*\d+\s*-?$', r'^\d{4}년도?\s*제\d+회\s*감정평가사\s*2차.*\(\s*\d+\s*-\s*\d+\s*\)\s*$',
    r'^\(\s*\d+\s*-\s*\d+\s*\)$', r'^\d+\s*-\s*\d+\s*\[\d교시\]$', r'^\d+\s*-\s*\d+$')]

def unwrap_layout_tables(md):
    """Replace HTML tables that contain a problem marker by their cell contents (layout wrappers)."""
    out = []; i = 0
    while True:
        k = md.find('<table', i)
        if k < 0: out.append(md[i:]); break
        out.append(md[i:k])
        # find matching </table>
        depth = 0; j = k
        for m in re.finditer(r'<table\b|</table>', md[k:]):
            depth += 1 if m.group(0).startswith('<table') else -1
            if depth == 0: j = k + m.end(); break
        else:
            j = len(md)
        tbl = md[k:j]
        if MARK.search(re.sub(r'<[^>]+>', '\n', tbl)) or '수험자 유의사항' in tbl:
            inner = tbl[tbl.find('>') + 1: tbl.rfind('</table>')]
            # cells -> paragraphs, keep nested tables
            inner = re.sub(r'</?t[rhd][^>]*>', '\n\n', inner) if '<table' not in inner else _cells(inner)
            inner = re.sub(r'<br\s*/?>', '\n', inner)
            out.append('\n\n' + unwrap_layout_tables(inner) + '\n\n')
        else:
            out.append(tbl)
        i = j
    return ''.join(out)

def _cells(inner):
    # split top-level cells while keeping nested tables intact
    res = []; depth = 0; buf = ''
    for tok in re.split(r'(<table\b[^>]*>|</table>|</?t[rhd][^>]*>)', inner):
        if tok is None: continue
        if tok.startswith('<table'): depth += 1; buf += tok
        elif tok == '</table>': depth -= 1; buf += tok
        elif re.fullmatch(r'</?t[rhd][^>]*>', tok) and depth == 0: buf += '\n\n'
        else: buf += tok
    return buf

def blocks_of(text):
    lines = text.split('\n'); out = []; i = 0
    while i < len(lines):
        s = lines[i]
        if '<table' in s:
            buf = []; depth = 0
            while i < len(lines):
                buf.append(lines[i]); depth += lines[i].count('<table') - lines[i].count('</table>')
                if depth <= 0: break
                i += 1
            t = '\n'.join(buf)
            if t.count('<table') > 1:  # nested tables: flatten inner ones to text
                out.append(('nested', t))
            else:
                out.append(('table', parse_html_table(t)))
            i += 1; continue
        if s.strip().startswith('|'):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                buf.append(lines[i]); i += 1
            out.append(('table', parse_gfm_table(buf))); continue
        m = re.fullmatch(r'\s*!\[[^\]]*\]\(([^)]+)\)\s*', s)
        if m: out.append(('img', m.group(1))); i += 1; continue
        st = re.sub(r'^#{1,6}\s*', '', s.strip())
        st = re.sub(r'^[-*+]\s+(?=※)', '', st)
        if st and not any(f.match(st) for f in FOOTER): out.append(('para', st))
        i += 1
    return out

md = MD.read_text(encoding='utf-8', errors='replace')
md = unwrap_layout_tables(md)
bl = blocks_of(md)
# split into problems
probs = []; pre = []; cur = None
for b in bl:
    t = b[1] if b[0] == 'para' else ''
    m = MARK.search(t) if b[0] == 'para' else None
    if m and (m.start() < 5 or t[:m.start()].strip() == ''):
        n = int(next(g for g in m.groups() if g))
        cur = {'n': n, 'blocks': [('para', t[m.end():].strip())]}; probs.append(cur); continue
    if m:  # marker in the middle of a line: split
        n = int(next(g for g in m.groups() if g))
        if cur: cur['blocks'].append(('para', t[:m.start()].strip()))
        else: pre.append(('para', t[:m.start()].strip()))
        cur = {'n': n, 'blocks': [('para', t[m.end():].strip())]}; probs.append(cur); continue
    (cur['blocks'] if cur else pre).append(b)

flags_all = []
folder, sko = SUBJ[PER]
d = REPO / folder / str(RND); d.mkdir(parents=True, exist_ok=True)
srcline = f'%% source: Q-Net 감정평가사 기출문제 (cst00309) artlSeq={src["source"].split("/")[2] if src else "?"} file={src["source"] if src else "?"}'

def emit(blocks, nn, flags):
    res = []; k = 0
    for b in blocks:
        if b[0] == 'para':
            if not b[1]: continue
            t = b[1]
            if re.match(r'^물음\s*\d+\)', t) or re.match(r'^\(\d+\)', t):
                res.append(BS + 'medskip' + BS + 'noindent ' + inline(t) + ' ' + BS + 'par')
            else:
                res.append(inline(t) + ' ' + BS + 'par')
        elif b[0] == 'table':
            flags.add('table'); res.append(grid_table_to_latex(b[1]))
        elif b[0] == 'nested':
            flags.add('nested-table')
            txt = re.sub(r'<br\s*/?>', '\n', b[1]); txt = re.sub(r'</t[hd]>', ' | ', txt); txt = re.sub(r'</tr>', '\n', txt)
            txt = html.unescape(re.sub(r'<[^>]+>', '', txt))
            res.append('% [자동 변환: 중첩 표를 평문으로 펼침 — 원문 대조 후 표 재구성 필요]\n' + BS + 'begin{framedtext}\n'
                       + '\n'.join(inline(x.strip()) + ' ' + BS + 'par' for x in txt.split('\n') if x.strip()) + '\n' + BS + 'end{framedtext}')
        elif b[0] == 'img':
            k += 1
            srcimg = (CONV / b[1]).resolve()
            try:
                im = Image.open(srcimg)
                if im.width < 40 or im.height < 20:
                    continue
                (d / 'figures').mkdir(exist_ok=True)
                name = f'{nn}-{k}.png'; im.save(d / 'figures' / name)
                flags.add('figure'); res.append(BS + 'qfigure{figures/' + name + '}')
            except Exception:
                flags.add('image-convert-failed')
    return '\n'.join(res)

if pre:
    fl = set()
    body = emit([b for b in pre if not (b[0] == 'para' and re.search(r'수험번호|성\s*명|감독자|시험시간|교\s*시|과목명|국가자격시험|문제지$|^\d{4}년도$', b[1]))], '00', fl)
    (d / '00.tex').write_text(f'%% kapa: exam=2 round={RND} year={YEAR} period={PER} subject={folder} subject_ko={sko} seq=0 kind=subject-instructions\n{srcline}\n'
                              f'%% conversion: kordoc 4.24.51 -> tools/gen2.py (auto); review=pending; flags={",".join(sorted(fl)) or "none"}\n'
                              f'%% 표지·공통 유의사항 등 문제 앞에 제시된 내용(표지의 수험번호/성명 칸은 제외)\n{body}\n', encoding='utf-8')
seen = set()
for p in probs:
    fl = set()
    nn = f'{p["n"]:02d}'
    if p['n'] in seen: fl.add('duplicate-problem-number'); nn += 'b'
    seen.add(p['n'])
    body = emit(p['blocks'], nn, fl)
    pts = re.search(r'\((\d+)\s*점\)', p['blocks'][0][1] if p['blocks'] and p['blocks'][0][0] == 'para' else '')
    if '「' not in body and re.search(r'(규칙|법률|기준|시행령)\s+[,，]', body): fl.add('possible-lost-brackets')
    tex = (f'%% kapa: exam=2 round={RND} year={YEAR} period={PER} subject={folder} subject_ko={sko} seq={p["n"]} number={p["n"]}'
           + (f' points={pts.group(1)}' if pts else '') + '\n' + srcline + '\n'
           + f'%% conversion: kordoc 4.24.51 -> tools/gen2.py (auto); review=pending; flags={",".join(sorted(fl)) or "none"}\n'
           + BS + 'begin{longquestion}{【문제 ' + str(p['n']) + '】}\n' + body + '\n' + BS + 'end{longquestion}\n')
    (d / f'{nn}.tex').write_text(tex, encoding='utf-8')
    flags_all.append({'round': RND, 'period': PER, 'subject': folder, 'number': p['n'], 'flags': sorted(fl), 'chars': len(body)})
nums = [p['n'] for p in probs]
exp = list(range(1, max(nums) + 1)) if nums else []
status = 'ok' if nums == exp else f'numbers={nums}'
print(RND, PER, folder, 'problems', len(probs), status, {f for x in flags_all for f in x['flags']})
with open(Q / 'meta' / 'flags2.jsonl', 'a', encoding='utf-8') as f:
    for x in flags_all: f.write(json.dumps(x, ensure_ascii=False) + '\n')
