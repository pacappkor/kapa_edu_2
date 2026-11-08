# 버전 규칙과 릴리스 절차

## 버전 규칙 (vMAJOR.MINOR.PATCH)

| 올리는 자리 | 이런 변경일 때 | 예 |
|---|---|---|
| MAJOR | 폴더 구조·파일명·`%% kapa:` 메타데이터 형식·`kapa-exam.sty` 매크로처럼 **문항 파일을 읽는 외부 코드나 문서가 깨지는** 변경 | 매크로 이름 변경 |
| MINOR | **새 시험 회차 추가**, 새 과목 추가, 새 도구·기능 추가 | 제38회(2027) 기출문제 추가 |
| PATCH | 문항 오탈자·표·그림 정정, 문서·도구 수정, 빌드 오류 수정 | 문항 하나의 오탈자 정정 |

- 1.0.0 전(0.x)에는 MAJOR 대신 MINOR 를 올린다. 이때 CHANGELOG 에 `### 호환성 깨짐` 절을 반드시 둔다.
- 버전 태그는 해당 PR 이 `main` 에 병합된 커밋에 단다. 형식은 `v0.1.0` 처럼 `v` 접두어를 붙인다.

## 새 회차 추가 절차

1. Q-Net 기출문제 게시판에서 새 회차 게시물을 확인한다. 작업 브랜치(`data/round-<회차>`)를 만든다.
   - 게시물: artlSeq, 첨부 형식
   - 이용 조건: 공공누리 표시
2. `tools/pipeline/` 로 수집·변환한다(README·AGENTS 의 절차와 `skills/kapa-past-exam`).
3. 문항마다 원본 페이지 이미지와 대조 교정한다. 끝나면 `review=proofread-*` 로 표시한다.
4. 검증:
   - `python -I tools/validate.py --write-status` → errors 0
   - `tools/build.py <과목>/<회차>` 컴파일
   - `text_crosscheck.py` 불일치 확인
5. `CHANGELOG.md` 의 `[Unreleased]` 에 아래 템플릿으로 항목을 쓴다. PR 을 연다(라벨 `data:collection`).
6. 병합 후:
   - 병합 커밋에 태그를 단다: `git tag -a vX.Y.0 <merge-commit> -m "..."` → `git push origin vX.Y.0`
   - CHANGELOG 의 해당 절을 본문으로 GitHub 릴리스를 만든다.

## 새 회차 항목 템플릿

```markdown
## [vX.Y.0] - YYYY-MM-DD

### 새 회차
| 회차 (연도) | 시행일 | 과목 | 문제 수 | 원본 (Q-Net artlSeq, 형식) | 교정 상태 |
|---|---|---|---|---|---|
| 제38회 (2027) | 2027-MM-DD | 감정평가실무·감정평가이론·감정평가 및 보상법규 | 12 | artlSeq=…, PDF | proofread 12 / pending 0 |

- 출처: 한국산업인력공단, Q-Net (공공누리 제1유형 표시 확인: 예/아니오)
- 변환 경로: PDF 텍스트 / HWP(rhwp) / OCR
- `\reviewflag` 남은 항목: 없음 / (파일 목록)

### 정정
| 파일 | 내용 | 근거 |
|---|---|---|
| `<과목>/<회차>/NN.tex` | … | 원본 페이지 이미지 / Q-Net 정정 공고 artlSeq=… |

### 변경
### 호환성 깨짐

### 검증
- `tools/validate.py`: errors 0 / warnings 0
- `tools/build.py`: N/N 컴파일, 누락 글리프 없음
- `text_crosscheck.py`: 비라벨 불일치 0
```

## 정정만 하는 릴리스 예시 (PATCH)

```markdown
## [v0.0.1] - YYYY-MM-DD
### 정정
| 파일 | 내용 | 근거 |
|---|---|---|
| `<과목>/25/12.tex` | ③ 선택지 오탈자 | 원본 페이지 이미지 (#이슈) |
```
