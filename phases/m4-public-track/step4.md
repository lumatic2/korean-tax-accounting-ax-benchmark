# Step 4: expert-review-protocol-scaffold

> ⏳ 후속 세션(이번 세션 미실행 — plan만). 외부 전문가 검수 도입을 시작한다. 현재 전 문항 `expert_review_required: true`(본인 검수 전 단계). M4 신뢰도를 위해 외부 세무·회계 전문가 검수 절차·기록 구조를 정식화한다.

## 읽어야 할 파일
- `docs/benchmark-schema.md` (§review, §status) — 왜: 검수 기록 필드(`reviewers`/`expert_reviewed_at`/`status: expert_reviewed`)와 상태 전이가 이미 스키마에 예약됨. 이를 채우는 절차 설계.
- `ROADMAP.md` (M4 "외부 전문가 검수 도입 시작" + M1 잔여 "본인 단독 검수 라운드") — 왜: 본인 검수 → 외부 검수의 2단계 순서.
- `CLAUDE.local.md` (전문가 검수 정식화 항목) — 왜: 신규 소득세 7문항(0013~0019) 본인 검수 대기 등 현 잔여.

## 작업 (착수 시)
- 검수 프로토콜 문서: 검수 대상 선정(공개셋 34 우선)·검수자 자격·체크리스트(정답·근거·루브릭·적시성)·이해상충 규칙.
- 기록 방식: `review.reviewers[]`에 검수자·일자·판정 추가, 통과 시 `status: expert_reviewed`·`version: 1.0` 승격.
- 본인 단독 검수 라운드(M1 잔여)를 먼저 클로즈한 뒤 외부 도입.

## Acceptance Criteria
```bash
# 착수 시 정의 — 검수 프로토콜 문서 + 1문항 expert_reviewed 파일럿
```

## 금지사항
- **본인 검수 미완 상태로 외부 검수 건너뛰기 금지.** 이유: ROADMAP 순서(본인→외부). 본인 검수가 1차 게이트.
- 검수 없이 `status: expert_reviewed` 승격 금지. 이유: 허위 신뢰자산 = 판매셋(M5) 리스크.
