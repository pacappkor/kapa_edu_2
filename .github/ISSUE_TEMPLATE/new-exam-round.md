---
name: 새 시험 회차 추가
about: Q-Net 에 새 감정평가사 제2차 시험 기출문제가 공개되었을 때
title: "새 회차 추가: 제___회 (20__) 제2차 시험"
labels: data:collection
---

## 원본
- 회차 / 연도 / 시행일:
- Q-Net 게시물 artlSeq (기출문제):
- 첨부 형식 (PDF/HWP):
- 공공누리 표시:

## 처리 체크리스트 (docs/RELEASING.md)
- [ ] 수집·변환
- [ ] 문항별 원본 대조 교정 (`review=proofread-*`)
- [ ] `validate.py --write-status` errors 0, `build.py` 컴파일, `text_crosscheck.py`
- [ ] CHANGELOG 항목 작성 → PR → 병합 → 태그·릴리스
