---
name: kapa-past-exam
description: 감정평가사(1차·2차) 기출문제와 최종 정답을 Q-Net 에서 수집해 문항별 LaTeX 로 변환하고 원본과 대조·검증하는 절차. 새 회차 추가, 기존 문항 교정, 정답 재확인, 처리 현황 갱신 작업에 사용한다.
---

# kapa-past-exam (초안)

## 언제 쓰나
- 새 회차 기출문제·정답이 Q-Net 에 올라왔을 때
- 자동 변환(`review=pending`) 문항을 원본과 대조해 교정할 때
- 정답표를 다시 판독·대조하거나 정답 정정을 반영할 때

## 입력
- 대상: 시험(1차/2차), 회차, (선택) 과목·문항 범위
- 저장소: 1차 `pacappkor/kapa_edu_1`, 2차 `pacappkor/kapa_edu_2` (비공개 유지)

## 절차
1. **사전 확인**
   - `gh repo view <repo> --json visibility` 로 PRIVATE 확인, 기본 브랜치·열린 PR·이슈·라벨 확인.
   - `docs/STATUS.md`, 관련 이슈를 읽고 중복 작업을 피한다.
2. **수집** (`tools/pipeline/qnet_fetch.py <작업폴더>`)
   - 기출 `code=1008`, 정답 `code=1206` 목록 → 상세(POST cst00302) → 첨부(cst00302s01).
   - 각 파일 SHA-256 을 기록하고 `docs/SOURCES.md` 에 추가. ZIP 은 별도 빈 폴더에 풀고 CP949 파일명 처리.
   - 다운로드 실패·형식 문제는 기록하고 가능한 범위의 작업을 계속한다.
3. **변환**
   - HWP → `npx kordoc x.hwp -o x.md`, 텍스트 PDF → `--no-tables`, 스캔 PDF → `--no-tables --ocr`(1차) / `--ocr`(2차).
   - 1차: `split1.py` → `gen1.py` (문항 분리·LaTeX 생성, flags 기록). 2차: `gen2.py` (【문제 N】 단위).
   - A/B형이 있으면 A형만.
4. **정답 (1차)**
   - 정답표는 그림인 경우가 많다. 서로 다른 두 판독자(예: 비전 모델 2종)가 독립 판독 → 대조 →
     불일치 칸은 원본을 확대해 확정. 결과를 `answers/answers.csv` 에 `verification` 과 함께 기록.
   - 최종 정답 우선. 복수 정답·전원 정답·정정은 정답표 원문 그대로 보존. 확인 못 하면 `?`(→ `\answerunknown`).
   - `python tools/apply_answers.py` 로 문항 파일에 반영.
5. **원본 대조 교정** — AGENTS.md §3 규칙. 페이지 PNG(PDF 는 PyMuPDF, HWP 는 rhwp `tools/pipeline/rhwp_pages.py`)를 보며 문두·선택지·표·그림·공통 지문 확인,
   `review=proofread-<검토자>` 로 갱신. 판단 불가 항목은 `\reviewflag{}`.
   그림은 TikZ/pgfplots 재현을 우선하고(빌드 PDF 를 원본과 나란히 비교), 불가능한 것만 PNG + `tools/optimize_figures.py`.
6. **검증**
   - `python tools/validate.py --write-status` (누락·번호·선택지 수·정답 일치)
   - `python tools/build.py <과목>/<회차>` (XeLaTeX 컴파일, 누락 글리프 확인)
   - 표본 PDF 를 원본과 나란히 육안 대조.
7. **이슈·라벨**: 해결 못 한 항목은 기존 이슈 검색 후 보완 또는 신규 등록(회차·과목·문항·출처·상황·확인·조치).
   라벨: `parse-error`, `missing-item`, `answer-check`, `figure-check`, `table-check`, `needs-review`, `license`.
8. **반영**: 작업 브랜치 → 커밋 → PR(범위·출처·검증 결과·미완료·관련 이슈 `Refs #N`, 라벨 `data:collection` 등).
   해결하지 않은 이슈에 `Closes` 를 쓰지 않는다.
9. **정리**: 업로드·검토 확인 후 내려받은 원본·임시 파일 삭제(복구에 필요한 매니페스트·해시는 저장소에 보존).

## 산출물 체크리스트
- [ ] 과목·회차 폴더에 01–40(1차) / 문제 수만큼(2차) 파일, `00.tex`(공통 지시문) 해당 시 포함
- [ ] 모든 문항 파일에 `%% kapa:` · `%% source:` · `%% conversion:` 줄
- [ ] (1차) 정답 줄 = answers.csv, `answerunknown` 0개 또는 이슈 등록
- [ ] 컴파일 성공, validate 오류 0
- [ ] STATUS.md · SOURCES.md 갱신, 이슈·PR 연결
