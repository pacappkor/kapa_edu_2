# 이용 조건 및 출처표시 (NOTICE)

이 저장소의 감정평가사 제2차 시험 기출문제(제19회 2008년 – 제37회 2026년)는
**한국산업인력공단**이 Q-Net 에 공개한 시험지에서 옮겼습니다. 공식 모범답안은 공개되지 않으며,
이 저장소에는 정답·해설이 없습니다. 공개된 자료라는 사실과 재이용 허락은 구분해야 합니다.

## 원자료의 출처와 회차별 이용 조건

- 출처: 한국산업인력공단, Q-Net 감정평가사 기출문제 게시판
  <https://www.q-net.or.kr/cst003.do?id=cst00309&gSite=L&gId=60>
- 회차·교시별 게시글 번호(artlSeq), 첨부파일명과 해시는 `docs/SOURCES.md` 에,
  문항별 출처는 각 파일의 `%% source:` 줄에 기록합니다.
- 근거 공지: 한국산업인력공단 「전문자격 기출문제 공공누리 적용 알림」
  (Q-Net 기출문제 게시판, artlSeq=5259147 첨부).
  공지는 "본 저작물(기출문제, 최종정답)은 '한국산업인력공단'에서 '(2014년 자료부터)'
  공공누리 제1유형으로 개방"한다고 밝힙니다. 이 인용은 2차 시험 공식 정답이 있다는 뜻이 아닙니다.

| 원자료 범위 | 확인된 근거와 이용 조건 |
|---|---|
| 제25–37회(2014–2026) 시험 문항 내용 | 위 Q-Net 공지가 밝힌 2014년 이후 자료의 공공누리 제1유형(출처표시) 개방 범위. 출처: 한국산업인력공단, Q-Net |
| 제19–24회(2008–2013) 시험 문항 내용 | `docs/SOURCES.md` 에 기록한 Q-Net 게시물에서 수집. 위 공지의 개방 범위 밖이며, 이 저장소에서는 별도 재이용 허락을 확인하지 못함. 공공누리 제1유형 또는 GPL 적용을 주장하지 않음 |

공공누리 제1유형은 출처표시 조건으로 상업적 이용 및 변경을 허용합니다.
조건 원문: <https://www.kogl.or.kr/info/licenseType1.do>.
2008–2013년 자료의 재이용·재배포 가능 여부는 권리자에게 별도로 확인해야 합니다.
저장소 관리자는 원자료에 새로운 이용 허락을 부여할 권한이 없으며, 저장소 공개 자체도 이용 허락이 아닙니다.

### 시험 그림과 PNG

문항의 문장·수치·표·그림 내용에는 위 회차별 원자료 조건이 적용됩니다.
원본에서 추출한 `figures/*.png` 도 해당 문항의 회차와 `%% source:` 에 기재된 시험지에서 온
원자료이며, 저장소가 새로 만든 GPL 그림으로 취급하지 않습니다. TikZ 로 재현한 그림도
코드에 대한 GPL 과 원자료 그림 내용의 권리는 별개입니다. 원자료 안에 별도 권리표시가 있는
제3자 그림 등은 그 표시와 권리를 추가로 확인해야 하며, 이 저장소는 별도 허락을 보증하지 않습니다.

## 저장소 고유 부분: GNU GPL v3.0

이 저장소가 더한 고유 작업물에는 **[GNU General Public License v3.0](LICENSE)(GPL-3.0-only)** 을 적용합니다.
- 문항의 LaTeX 변환·조판 코드: LaTeX 구조, TikZ 재현 코드, `latex/` 스타일
- 도구: `tools/` 의 수집·변환·검증·빌드 코드
- 저장소의 구성: 폴더 체계, 메타데이터 형식
- 문서: README, AGENTS, docs, skills

이 부분을 복제·수정해 배포하려면 GPL v3.0 조건을 따릅니다. 수정본에도 같은 라이선스를 적용하고,
소스를 공개하며, 이 고지를 유지해야 합니다. GPL 은 원자료나 제3자 저작물에 대한 권리를 부여하거나
원자료의 이용 조건을 바꾸지 않습니다. 혼합된 자료를 재배포할 때는 GPL 과 해당 원자료의 조건을 각각 확인해야 합니다.

```text
kapa_edu_2 — 감정평가사 제2차 기출문제 LaTeX 저장소 (저장소 고유 작업물)
Copyright (C) 2026 pacappkor
This program is free software: you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation, version 3.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
License for more details. You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.
```
