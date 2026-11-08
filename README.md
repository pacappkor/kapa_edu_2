# kapa_edu_2 — 감정평가사 제2차 시험 기출문제 (LaTeX)

Q-Net(한국산업인력공단)에 공개된 **감정평가사 제2차 시험** 기출문제를 과목별·회차별·문제별 LaTeX 조각 파일로
정리한 저장소입니다. 2차 시험은 논술형이므로 공식 정답이 공개되지 않으며, 이 저장소에도 정답·해설은 없습니다.

- 범위: 제19회(2008) – 제37회(2026), 19개 회차 × 3과목(교시)
- 처리 현황: [`docs/STATUS.md`](docs/STATUS.md) (자동 생성) · 출처 목록: [`docs/SOURCES.md`](docs/SOURCES.md)
- 작업 절차: [`AGENTS.md`](AGENTS.md) · skill 초안: [`skills/kapa-past-exam/SKILL.md`](skills/kapa-past-exam/SKILL.md)

> ℹ️ 229개 문제 모두 원본(시험지 PDF/HWP 페이지 이미지)과 대조 교정을 마쳤습니다(`review=proofread-*`). 교정은 AI 에이전트가 수행했으며
> 사람의 표본 검수는 아직입니다(관련 이슈).

## 자료 출처와 이용 조건
- 기출문제: Q-Net 감정평가사 › 기출문제 내려받기 <https://www.q-net.or.kr/cst003.do?id=cst00309&gSite=L&gId=60>
- 게시글 번호(artlSeq)·첨부파일명·SHA-256: `docs/SOURCES.md`, 각 파일의 `%% source:` 줄.
- **이용 조건**: 문항·정답 내용은 전 회차 **공공누리 제1유형(출처표시)**, 이 저장소의 변환·조판 코드·도구·문서는 **[GPL-3.0](LICENSE)** — 출처: 한국산업인력공단, Q-Net. 자세한 내용과 적용 근거는 [`NOTICE.md`](NOTICE.md). Q-Net 공지는 2014년 자료부터 제1유형 개방을 밝히고 있으며, 2013년 이전(제19–24회) 자료에도 저장소 관리자 결정으로 같은 조건을 일괄 적용합니다. 저장소 공개 여부는 별도로 관리자가 결정합니다(현재 비공개).
- 원본 시험지(PDF/HWP)는 저장소에 넣지 않습니다.

## 디렉터리 구조와 과목 대응

```text
<subject>/<round>/NN.tex      문제 파일 (NN = 시험지의 【문제 NN】 번호)
<subject>/<round>/00.tex      문제 1 앞에 인쇄된 공통 유의사항(있을 때). 표지의 수험자 유의사항·안내문은 제외
<subject>/<round>/figures/    그림 (NN-k.png) — TikZ 로 재현하지 못한 그림만(사진·지적도 등)
latex/kapa-exam.sty           공통 스타일 (1차 저장소와 동일 파일)
tools/build.py                과목·회차별 묶음 PDF 빌드 / 컴파일 검증
tools/validate.py             구조 검증 + docs/STATUS.md 생성
tools/optimize_figures.py     남은 PNG 그림 용량 최적화
tools/pipeline/               수집·변환 스크립트 (gen2.py, mdtex.py)
subjects.json                 폴더명 ↔ 과목명 대응표
```

| 폴더 | 과목 | 교시 |
|---|---|---|
| `appraisal_practice` | 감정평가실무 | 1교시 |
| `appraisal_theory` | 감정평가이론 | 2교시 |
| `compensation_law` | 감정평가 및 보상법규 | 3교시 |

## 문제 파일 규칙

```latex
%% kapa: exam=2 round=37 year=2026 period=2 subject=appraisal_theory subject_ko=감정평가이론 seq=1 number=1 points=40
%% source: Q-Net 감정평가사 기출문제 (cst00309) artlSeq=5268128 file=raw/1008/5268128/…(2교시_감정평가이론).pdf
%% conversion: kordoc 4.24.51 -> tools/gen2.py (auto); review=pending; flags=none
\begin{longquestion}{【문제 1】}
… (40점) \par
\medskip\noindent 물음 1) … (20점) \par
\end{longquestion}
```

- 한 파일 = 시험지의 【문제 N】 하나(하위 물음·자료·표·그림 포함). 배점은 본문 그대로, 메타데이터 `points` 에도 기록.
- 프리앰블 없는 조각 파일입니다. 다른 문서에 넣을 때는 `\usepackage{kapa-exam}` 후
  `\subimport{<subject>/<round>/}{NN.tex}` (그림 경로가 상대경로이므로 `\subimport` 사용).
- 표는 `tabular`(병합 칸 `\multirow`/`\multicolumn`), 테두리 상자(참조 조문 등)는 `framedtext`, 그림은 `\qfigure`.
- `review` 값: `pending`(자동 변환) / `proofread-<검토자>`(원본 이미지 대조 교정 완료). flags 의미는 AGENTS.md.

### 그림
- 그래프·도식·단순 도면은 문항 파일 안에 **TikZ/pgfplots** 로 재현합니다(라벨·눈금·선 모양을 원본과 동일하게, 원본 대조 후 `flags` 에 `tikz`).
- 정확한 재현이 어려운 그림만 `figures/NN-k.png` 로 두고 `\qfigure` 로 넣으며, `python tools/optimize_figures.py` 로 용량을 줄입니다. SVG 는 XeLaTeX 에서 직접 쓸 수 없어 사용하지 않습니다.

## 빌드 및 검토
필요: TeX Live 2024 이상(XeLaTeX, kotex, unfonts-core), Python 3.10+.

```bash
python tools/build.py                          # 전체
python tools/build.py appraisal_practice/37    # 과목·회차
python tools/validate.py --write-status        # 구조 검증 + STATUS.md 갱신
```
검토는 `build/` PDF 와 원본 시험지를 나란히 놓고 문제 번호·본문·물음·배점·표(모든 칸)·그림을 대조합니다.

## 버전과 변경 이력

- 변경 내용: [CHANGELOG.md](CHANGELOG.md)
- 버전 규칙과 새 회차 추가 절차: [docs/RELEASING.md](docs/RELEASING.md)
  - 새 시험 회차를 추가하면 MINOR 를 올린다.
