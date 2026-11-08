# SPDX-License-Identifier: GPL-3.0-only
"""Markdown(kordoc) -> LaTeX inline/block conversion helpers shared by exam1/exam2 converters."""
import re, html

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"
SPECIAL = {'\\': r'\textbackslash{}', '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&', '_': r'\_',
           '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}

def esc_plain(s):
    return ''.join(SPECIAL.get(c, c) for c in s)

MATH_RE = re.compile(r'(\$\$.+?\$\$|\$[^$\n]+?\$)', re.S)

def fix_math(m):
    m = re.sub(r'\s*_\s*\{', '_{', m); m = re.sub(r'\s*\^\s*\{', '^{', m)
    # leftovers of HWP equation-editor syntax (typography keywords only)
    m = re.sub(r'\b(?:bold|rm|it)\s*(?=[\{A-Za-z])', '', m)
    # balance braces inside one math segment
    inner = m.strip('$'); depth = 0; out = ''
    for ch in inner:
        if ch == '{': depth += 1
        elif ch == '}':
            if depth == 0: continue
            depth -= 1
        out += ch
    out += '}' * depth
    d = '$$' if m.startswith('$$') else '$'
    return d + out + d

def inline(s):
    """Convert one markdown inline string to LaTeX (keeps $math$)."""
    s = s.replace('\\.', '.').replace('\\*', '*').replace('\\-', '-').replace('\\(', '(').replace('\\)', ')')
    s = s.replace('\\[', '[').replace('\\]', ']').replace('\\#', '#').replace('\\_', '_').replace('\\|', '|')
    s = s.replace('\\$', '\x00')  # markdown-escaped literal dollar
    out = []
    # segments: (is_math, text). A "$...$" span containing Hangul is not math: its dollars are literal.
    segs = []
    for i, part in enumerate(MATH_RE.split(s)):
        is_math = i % 2 == 1 and not re.search(r'[가-힣]', part)
        if not is_math:
            part = part.replace('$', '\x00')
            if segs and not segs[-1][0]:
                segs[-1] = (False, segs[-1][1] + part); continue
        segs.append((is_math, part))
    for is_math, part in segs:
        if is_math:
            out.append(fix_math(part)); continue
        part = html.unescape(part)
        # protect tags
        toks = re.split(r'(<br\s*/?>|</?(?:u|b|strong|i|em|sup|sub|s|del)>|\*\*)', part)
        state = []
        for t in toks:
            if t is None or t == '':
                continue
            tl = t.lower()
            if re.fullmatch(r'<br\s*/?>', tl): out.append(r'\newline{}')
            elif tl in ('<u>',): out.append(r'\uline{')
            elif tl in ('<b>', '<strong>'): out.append(r'\textbf{')
            elif tl in ('<i>', '<em>'): out.append(r'\textit{')
            elif tl == '<sup>': out.append(r'\textsuperscript{')
            elif tl == '<sub>': out.append(r'\textsubscript{')
            elif tl in ('<s>', '<del>'): out.append(r'\sout{')
            elif tl in ('</u>', '</b>', '</strong>', '</i>', '</em>', '</sup>', '</sub>', '</s>', '</del>'): out.append('}')
            elif t == '**':
                if state and state[-1] == '**': state.pop(); out.append('}')
                else: state.append('**'); out.append(r'\textbf{')
            elif t == '__':
                out.append(r'\_\_')
            else:
                # 4+ consecutive spaces or 3+ underscores in source = blank to fill (밑줄 빈칸) in the original
                e = esc_plain(t)
                e = re.sub(r'(?:\\_){3,}', lambda m: '\\blank{}', e)
                out.append(re.sub(r' {4,}', lambda m: ' \\blank{} ', e))
        out.extend('}' for _ in state)
    r = ''.join(out).replace('\x00', r'\$')
    r = re.sub(r'(\\_){2,}(?=\\_)|(?:\\_\\_)+', lambda m: '\\blank{}' if len(m.group(0)) >= 6 else m.group(0), r)
    return r

# ---------------- tables ----------------
def parse_html_table(t):
    rows = []
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
        cells = []
        for m in re.finditer(r'<(td|th)([^>]*)>(.*?)</\1>', tr, re.S):
            attrs = m.group(2)
            rs = int((re.search(r'rowspan="?(\d+)', attrs) or [0, 1])[1])
            cs = int((re.search(r'colspan="?(\d+)', attrs) or [0, 1])[1])
            cells.append((m.group(3).strip(), rs, cs))
        rows.append(cells)
    return rows

def parse_gfm_table(lines):
    rows = []
    for ln in lines:
        ln = ln.strip()
        if re.fullmatch(r'\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?', ln):
            continue
        if ln.startswith('|'): ln = ln[1:]
        if ln.endswith('|') and not ln.endswith('\\|'): ln = ln[:-1]
        cells = [c.strip() for c in re.split(r'(?<!\\)\|', ln)]
        rows.append([(c, 1, 1) for c in cells])
    return rows

def grid_table_to_latex(rows):
    """rows: list of list of (text, rowspan, colspan). Emits tabular with multirow/multicolumn."""
    # compute grid
    occ = {}
    placed = []
    ncols = 0
    for r, cells in enumerate(rows):
        c = 0
        for (txt, rs, cs) in cells:
            while (r, c) in occ: c += 1
            placed.append((r, c, txt, rs, cs))
            for dr in range(rs):
                for dc in range(cs):
                    occ[(r + dr, c + dc)] = (r, c)
            c += cs
            ncols = max(ncols, c)
    nrows = len(rows)
    ncols = max(ncols, max((c + 1 for (_, c) in occ), default=1))
    start = {(r, c): (txt, rs, cs) for (r, c, txt, rs, cs) in placed}
    lines = []
    for r in range(nrows):
        parts = []
        c = 0
        while c < ncols:
            if (r, c) in start:
                txt, rs, cs = start[(r, c)]
                body = r'\makecell{' + inline(txt) + '}' if txt else ''
                if rs > 1: body = r'\multirow{%d}{*}{%s}' % (rs, body)
                if cs > 1: body = r'\multicolumn{%d}{|c|}{%s}' % (cs, body)
                parts.append(body); c += cs
            elif (r, c) in occ:
                orr, occ_c = occ[(r, c)]
                txt, rs, cs = start[(orr, occ_c)]
                parts.append(r'\multicolumn{%d}{|c|}{}' % cs if cs > 1 else '')
                c += cs
            else:
                parts.append(''); c += 1
        # cline: rows where a multirow continues should not draw full hline
        lines.append(' & '.join(parts) + r' \\')
        cont = [c for c in range(ncols) if (r + 1, c) in occ and occ[(r + 1, c)][0] <= r]
        if cont:
            segs = []; c = 0
            while c < ncols:
                if c in cont: c += 1; continue
                s = c
                while c < ncols and c not in cont: c += 1
                segs.append(r'\cline{%d-%d}' % (s + 1, c))
            lines.append(' '.join(segs))
        else:
            lines.append(r'\hline')
    spec = '|' + 'c|' * ncols
    return '{\\small\\centering\n\\begin{tabular}{%s}\n\\hline\n%s\n\\end{tabular}\\par}\n' % (spec, '\n'.join(lines))
