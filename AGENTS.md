# AGENTS.md — 작업 가이드 (사람·AI 에이전트 공통) — 2차 시험

이 저장소는 관리자 결정에 따라 **공개할 수 있습니다**. 공개 여부와 관계없이 자격증명·토큰·비밀번호는 절대 커밋하지 않습니다.
원자료(그림 PNG 포함)의 출처는 한국산업인력공단, Q-Net 입니다. 제25–37회(2014–2026)는 Q-Net 공지의 공공누리 제1유형 개방 범위이며, 제19–24회(2008–2013)는 별도 재이용 허락을 확인하지 못했습니다. 관리자가 원자료에 이용 허락을 부여하지 않습니다. 회차별 근거와 제한은 `NOTICE.md` 를 따릅니다. 저장소 고유 작업물(LaTeX 변환·조판 코드, `tools/`, 문서)은 GPL-3.0-only(`LICENSE`)이며, 새 코드 파일에는 `SPDX-License-Identifier: GPL-3.0-only` 를 답니다. 새 회차는 출처와 실제 이용 조건을 확인·기록하고 기존 조건을 임의로 확대하지 않습니다. 기본 브랜치에 직접 커밋하지 말고 작업 브랜치 + PR 로 반영합니다.

## 0. 원칙
1. **원본이 유일한 기준**입니다. 원본(Q-Net 시험지 PDF/HWP, 정답표)에 없는 내용·정답을 추정해서 채우지 않습니다.
   원본의 오탈자도 그대로 두고 필요하면 `% [원문 그대로]` 주석을 답니다.
2. 확인할 수 없는 부분은 문항 안에 `\reviewflag{사유}` 를 남기고 GitHub 이슈로 등록합니다.
3. 2차 시험은 공식 정답이 없으므로 정답·해설을 추가하지 않습니다.
4. 토큰·비밀번호 등 비밀값을 커밋·로그·PR·이슈에 남기지 않습니다.

## 1. 자료 수집
- 기출문제 게시판: `cst00309`, 정답 게시판: `cst00310` (README 의 URL).
  목록은 `cst003.do?id=cst00301s01&gSite=L&gId=60&page=N&boardId=Q004&code=1008`(기출) / `code=1206`(정답) 으로 조회되고,
  상세는 `cst00302` 에 POST(artlSeq, boardId=Q004, code, menuType), 첨부는 `cst00302s01`(filePath, fileName, fileSeq, artlSeq) 로 받습니다.
  스크립트: `tools/pipeline/qnet_fetch.py` (목록·상세·첨부 일괄 다운로드, SHA-256 기록).
- 내려받은 파일은 저장소 밖의 빈 작업 폴더에 둡니다(신뢰할 수 없는 입력). ZIP 내부 파일명은 CP949 일 수 있습니다.
- 새 회차가 올라오면 `docs/SOURCES.md` 에 게시글 번호·파일명·SHA-256 을 추가합니다.

## 2. 변환

HWP 는 두 도구를 함께 씁니다: **kordoc**(본문·수식 추출, 수식이 LaTeX 로 나옴)과 **rhwp**(페이지 렌더링 → 원본 대조용 이미지, `export-tables` 로 표·표 형태 선택지 구조 확인). 2026-11 샘플 비교에서 rhwp `export-markdown` 은 수식이 HWP 수식 문법(`pi ^{e}`, `LEFT {`)으로 나오고 화면 줄바꿈이 섞여 본문 추출 기본 도구로는 kordoc 을 유지했습니다.

| 원본 형식 | 도구 | 비고 |
|---|---|---|
| HWP (제19–25회) | kordoc (`npx kordoc file.hwp -o out.md`) | 표·수식 품질 높음 |
| 텍스트 PDF (제26, 27, 29–31, 33, 34, 36, 37회, 제28회 1교시) | kordoc (기본: 표 유지) | 문제 전체를 감싼 레이아웃 표는 gen2.py 가 풀어냄. 중첩 표는 평문으로 펼쳐지므로 재구성 필요 |
| 스캔 PDF (제28회 2·3교시, 제32회, 제35회) | kordoc `--ocr` | OCR 오류(甲·乙 누락, 띄어쓰기, 숫자) 많음 → **전수 교정 필수**. 제32·35회는 3개 교시가 한 파일 |

- 문제 분리·LaTeX 생성: `tools/pipeline/gen2.py <작업폴더> <저장소> <회차> <교시 1|2|3> <md 파일>` — 【문제 N】/【문 N】 표지로 분리.
- 생성 직후 `python tools/validate.py`, `python tools/build.py <과목>/<회차>` 를 실행합니다.

## 3. 교정(원본 대조) 절차
1. 원본 페이지를 PNG 로 렌더링(130 dpi 이상)합니다. PDF 는 PyMuPDF, **HWP 는 rhwp**(`tools/pipeline/rhwp_pages.py`,
   <https://github.com/edwardkim/rhwp> v0.8.7, 릴리스 바이너리를 SHA256SUMS 로 검증 후 사용)로 렌더링합니다.
   rhwp 렌더링은 글꼴 차이로 쪽·단 배치가 원본과 다르고 꼬리말이 끝 줄과 겹칠 수 있으나 내용은 원본 그대로입니다.
2. 문제마다 확인: 번호 · 본문 · 물음(배점) · 자료 · 표(모든 칸·병합) · 수식 · 그림 · 참조 조문 상자 · 페이지 경계 이음.
3. 표기 규칙
   - 보기 상자(〈보기〉 제목) → `\begin{bogi} … \end{bogi}`, 제목 없는 테두리 지문 → `framedtext`
   - 표 → `tabular` (`{\small\centering\begin{tabular}{|c|c|}…\end{tabular}\par}`)
   - 밑줄 → `\uline{}`, 빈칸 → `\blank{}`, 수식 → `$…$`
   - 그림 → **TikZ/pgfplots 로 문항 파일 안에 재현하는 것이 원칙**입니다(그래프·도식·단순 도면). 모든 라벨·눈금 값·
     기호·점선/실선·교점 관계를 원본과 같게 그리고, 원본에 없는 정보는 넣지 않습니다. 재현 후 빌드한 PDF 를 원본과
     나란히 보고 확인하며 `flags` 에 `tikz` 를 적습니다.
     정확한 재현이 어려운 사진·지적도·복잡한 도면만 원본에서 잘라 `figures/NN-k.png` 로 두고
     `\qfigure[너비]{figures/NN-k.png}` 로 넣습니다(커밋 전 `python tools/optimize_figures.py` 로 용량 최적화).
     SVG 는 XeLaTeX 에서 직접 넣을 수 없어(컴파일마다 Inkscape 필요) 사용하지 않습니다.
   - LaTeX 특수문자 `% $ & # _ { }` 는 이스케이프
4. 교정을 마친 파일은 `%% conversion:` 줄의 `review=pending` 을 `review=proofread-<검토자>` 로 바꾸고
   `flags=` 는 남은 확인 사항만(없으면 `none`) 적습니다. `%% kapa:` · `%% source:` 줄은 바꾸지 않습니다.
5. 과목·회차 단위로 `python tools/build.py <과목>/<회차>` 컴파일, `python tools/validate.py` 통과 확인.
6. 원문 대조(자동): `python -I tools/pipeline/text_crosscheck.py . <원본텍스트폴더>` — 문항 파일의 한글 낱말이 원본 텍스트층(텍스트 PDF 는 PyMuPDF, HWP 는 rhwp `export-text`)에 실제로 있는지 확인합니다. 원본에 없는 낱말은 '원문 변경' 의심이므로 이미지로 확인합니다(TikZ 그림 라벨처럼 원래 텍스트층에 없는 글자는 정상). 원문 오탈자를 '교정'하지 않았는지 확인하는 데 씁니다.
7. HWP 회차는 rhwp 렌더링이 일부 글자(여는 따옴표 ‘ “ 등)를 빠뜨리거나 줄을 겹쳐 그리는 일이 있습니다. **렌더링에만 없는 글자는 원문 근거가 아닙니다** — 글자는 HWP 텍스트(rhwp `export-text`)로, 구조(상자·표·배치)는 이미지로 확인합니다.

## 4. 기여(PR) 절차
- 기본 검토 소유자는 `.github/CODEOWNERS` 에 지정한다.
- 문서(Markdown)에서 범위는 "–"(en dash)로 씁니다(예: 제19–37회). `~` 는 GitHub 에서 취소선이 되므로 코드 스팬 밖에서 쓰지 않습니다(`validate.py` 가 검사).
1. `git switch -c <type>/<요약>` (예: `fix/practice-26-tables`, `data/round-38`)
2. 커밋 메시지: `<과목>/<회차>: <무엇을>` (예: `appraisal_practice/26: 문제 1 자료 3 표 재구성`)
3. PR 본문: 범위(회차·과목·문항), 대조한 원본, 검증 결과(validate/build), 남은 문제와 관련 이슈.
   해결하지 못한 이슈는 `Refs #N` 으로 연결하고 **`Closes`/`Fixes` 는 실제로 해결한 이슈에만** 씁니다.
4. `python tools/validate.py --write-status` 로 `docs/STATUS.md` 를 갱신해 함께 커밋합니다.

## 5. 이슈·라벨
- 새 이슈 전에 기존 이슈를 검색합니다. 원인과 해결 방법이 같은 항목은 한 이슈로 묶되 회차·과목·문항을 표로 적습니다.
- 이슈 본문 필수 항목: 회차 · 과목 · 문항 번호 · 자료 출처(artlSeq/파일) · 문제 상황 · 수행한 확인 · 후속 조치.
- 라벨

| 라벨 | 용도 |
|---|---|
| `data:collection` | 자료 수집·정리 작업(PR) |
| `parse-error` | 파싱·OCR 오류, 깨진 문자·수식 |
| `missing-item` | 누락 문항·원본 자료 미확보 |
| `figure-check` | 그림 추출·재현 확인 필요 |
| `table-check` | 표 구조 재구성 필요 |
| `needs-review` | 원본 대조 검토 필요 |
| `license` | 저작권·이용 조건 확인 |
| `documentation` | 문서 (GitHub 기본 라벨) |

## 6. flags 사전 (`%% conversion:` 줄)
| flag | 의미 / 조치 |
|---|---|
| `table` | 표를 자동 변환함. 병합 칸·정렬·숫자 확인 |
| `nested-table` | 중첩 표를 평문으로 펼침 → 원본 대조 후 tabular 재구성 |
| `figure` | 그림을 추출해 포함함. 표지 로고·QR 코드 등 불필요한 그림이 섞였을 수 있음 |
| `possible-lost-brackets` | 「」 기호가 빠졌을 가능성(법령명 뒤 공백·쉼표) |
| `duplicate-problem-number` | 같은 문제 번호가 두 번 감지됨 → 분리 확인 |
| `tikz` | 원본 그림을 TikZ/pgfplots 로 재현함(원본 대조 완료) |

## 버전과 변경 이력

변경은 `CHANGELOG.md` 의 `[Unreleased]` 에 기록한다. 버전 규칙과 새 회차 추가·릴리스 절차는 `docs/RELEASING.md` 에 있다.
- 새 회차는 MINOR, 정정은 PATCH, 폴더·메타데이터·매크로 변경은 호환성 깨짐이다.
