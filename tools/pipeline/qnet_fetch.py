#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Q-Net 감정평가사 기출문제(code=1008)·최종정답(code=1206) 게시판 수집.

usage: python -I qnet_fetch.py <작업폴더>
  <작업폴더>/meta/posts.json      게시글·첨부 목록
  <작업폴더>/meta/detail_*.html   상세 페이지 원문
  <작업폴더>/raw/<code>/<artlSeq>/<첨부파일>
  <작업폴더>/meta/sha256.tsv      첨부파일 해시
작업폴더는 저장소 밖의 빈 폴더를 쓰세요(내려받은 파일은 신뢰할 수 없는 입력).
"""
import re, html, json, sys, time, hashlib, pathlib, urllib.request, urllib.parse, http.cookiejar

BASE = 'https://www.q-net.or.kr/'
OUT = pathlib.Path(sys.argv[1]); META = OUT / 'meta'; RAW = OUT / 'raw'
META.mkdir(parents=True, exist_ok=True)
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]

def fetch(url, data=None, binary=False):
    for i in range(5):
        try:
            r = op.open(url, data=urllib.parse.urlencode(data).encode() if data else None, timeout=120).read()
            return r if binary else r.decode('utf-8', 'replace')
        except Exception as e:
            print('retry', url[:80], e, file=sys.stderr); time.sleep(5)
    raise RuntimeError(url)

fetch(BASE + 'cst003.do?id=cst00309&gSite=L&gId=60')
result = {}
for code, menu in (('1008', 'cst00309'), ('1206', 'cst00310')):
    posts, seen = [], set()
    for page in range(1, 50):
        t = fetch(BASE + f'cst003.do?id=cst00301s01&gSite=L&gId=60&page={page}&schText=&schType=&boardId=Q004&code={code}')
        found = re.findall(r"goNext\('(\d+)',\s*'(\d+)',\s*'(\w*)'\)", t)
        if not found: break
        for seq, _, cst in found:
            if seq not in seen:
                seen.add(seq); posts.append({'artlSeq': seq, 'cst': cst})
        time.sleep(0.5)
    for p in posts:
        d = fetch(BASE + 'cst003.do?id=cst00302&gSite=L&gId=60', {'page': '1', 'schType': '', 'schText': '', 'artlSeq': p['artlSeq'],
                  'boardId': 'Q004', 'code': code, 'menuType': menu, 'cst': p['cst']})
        (META / f'detail_{code}_{p["artlSeq"]}.html').write_text(d, encoding='utf-8')
        cand = re.findall(r'>([^<>]{0,60}(?:제\s*\d+\s*회|\d{2,4}년)[^<>]{0,80})<', d)
        p['title'] = html.unescape(cand[0].strip()) if cand else ''
        p['files'] = [{'path': a, 'name': b, 'seq': c} for a, b, c in re.findall(r"fileDown\('([^']*)',\s*'([^']*)',\s*'([^']*)'\)", d) if '+' not in a]
        time.sleep(0.5)
    result[code] = posts
(META / 'posts.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
with open(META / 'sha256.tsv', 'w', encoding='utf-8') as h:
    for code, posts in result.items():
        for p in posts:
            for f in p['files']:
                dest = RAW / code / p['artlSeq'] / f['name'].replace('`', '').strip()
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not (dest.exists() and dest.stat().st_size):
                    q = urllib.parse.urlencode({'id': 'cst00302s01', 'gSite': 'L', 'gId': '60', 'fileCode': 'R001', 'filePath': f['path'],
                                                'fileName': f['name'], 'fileSeq': f['seq'], 'artlSeq': p['artlSeq'], 'href': '0'})
                    dest.write_bytes(fetch(BASE + 'cst003.do?' + q, binary=True)); time.sleep(0.7)
                h.write(f"{code}\t{p['artlSeq']}\t{p['title']}\t{dest.relative_to(OUT).as_posix()}\t{hashlib.sha256(dest.read_bytes()).hexdigest()}\n")
print({k: len(v) for k, v in result.items()})
