# Step 1: leaderboard-submission-policy-adr

> 로컬·무billing. 공개 리더보드의 **제출·철회·재현 검증 정책**을 ADR로 확정한다. 「The Leaderboard Illusion」(Chatbot Arena 분석)의 실패모드 — 비공개 재시도 후 best-pick, 모델 철회로 표본 조작, 데이터 접근 비대칭, 과적합 — 를 구조적으로 차단하는 규칙을 박는다. 코드 구현이 아니라 정책 결정.

## 읽어야 할 파일
- `docs/m4-public-sample-scope.md` (step0 산출) — 왜: 공개셋(34) vs 채점 holdout(58)의 분리가 정책의 토대. 리더보드 점수는 holdout으로 매기고 공개셋은 연습용임을 정책에 반영.
- `ROADMAP.md` (M4 "제출 정책·철회 규칙 명문화(「Leaderboard Illusion」 교훈)") — 왜: 이 ADR이 충족할 마일스톤 항목의 원문.
- `docs/adr/README.md` + `docs/adr/0008-agent-eval-isolation.md` — 왜: ADR 포맷(Status/Context/Decision/Consequences)·번호 규칙(다음=0009)·문체 레퍼런스.
- `CLAUDE.md` (§⚠ Judge 규약) — 왜: self-eval 천장 회피 원칙이 "제출 점수는 본인/외부 권위 검증" 규칙으로 ADR에 들어가야 함.

## 작업
### ADR 0009 작성 — `docs/adr/0009-leaderboard-submission-policy.md`
Michael Nygard 4섹션. 다음 결정들을 포함(각각 Leaderboard Illusion 실패모드와 1:1 대응):
- **Context**: 왜 정책이 필요한가 — Arena류에서 관측된 4대 조작(① 비공개 N회 재시도 best-pick ② 선택적 철회로 손실 표본 은폐 ③ proprietary 데이터 접근 비대칭 ④ 공개 테스트셋 과적합).
- **Decision**:
  1. **제출 단위 = 버전핀 고정** — 모델 id·날짜·scaffold(prompt_version)·mode를 제출시 동결. 같은 모델 재제출은 새 행(덮어쓰기 금지) → 재시도 best-pick 차단.
  2. **점수는 holdout으로만** — 공개셋(34)은 연습/디버그용, 순위는 비공개 holdout(58)+로테이션. 공개셋 점수는 별도 표기(과적합 가시화).
  3. **철회 규칙** — 한번 게시된 결과는 철회 불가(아카이브로 회색표시만). 표본 선택적 은폐 차단.
  4. **재현 검증** — 제출 결과는 버전핀으로 본인이 재실행 가능해야 등재(self-report 금지). judge는 비self 모델 고정.
  5. **접근 대칭** — 모든 제출자는 동일 공개셋·동일 실행기. 비공개 데이터 우대 없음.
- **Consequences**: 운영 비용(매 제출 재현=billing), 투명성 이득, 한계(초기엔 본인이 모든 제출 대행).

## Acceptance Criteria
```bash
test -f docs/adr/0009-leaderboard-submission-policy.md && echo "adr OK"
# 4섹션 헤더 존재
grep -qE '^## (Status|상태)' docs/adr/0009-leaderboard-submission-policy.md && grep -qiE 'Context|Decision|Consequence|맥락|결정|결과' docs/adr/0009-leaderboard-submission-policy.md && echo "sections OK"
# 4대 실패모드가 모두 언급되는지(재시도/철회/접근/과적합)
grep -qE '재시도|best-pick' docs/adr/0009-leaderboard-submission-policy.md && grep -q '철회' docs/adr/0009-leaderboard-submission-policy.md && echo "failure modes OK"
```

## 검증 절차
1. AC 실행.
2. ADR README 인덱스에 0009 행 추가(supersede 아닌 신규).
3. 각 Decision 항목이 Leaderboard Illusion 실패모드와 매핑되는지 self-check(매핑 표 1개 포함).
4. `phases/m4-public-track/index.json` step 1 → `completed` + `summary`.

## 금지사항
- **정책을 코드로 구현하지 마라.** 이유: 이 step은 결정(ADR)만. 구현은 step3(웹) 범위.
- **self-report 점수 등재를 허용하는 문구 금지.** 이유: Judge 규약 self-eval 천장 — 점수는 재현 검증된 것만.
- ADR 본문은 한번 쓰면 수정 X(README 가이드). 초안 단계라도 결정형으로 단정해 쓰되, 미정 사항은 "Consequences/한계"에 명시.
- 공개셋으로 순위를 매기는 정책 금지. 이유: 과적합 = Leaderboard Illusion 핵심 실패. 순위는 holdout.
