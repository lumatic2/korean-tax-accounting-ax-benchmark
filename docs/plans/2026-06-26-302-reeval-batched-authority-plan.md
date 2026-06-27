# 302 재평가 milestone plan — batched authority evaluation

> 상태: active milestone execution. `closed_book` 302-run은 완료했고, `authority_rag` 후보 생성 및 공개 배포는 남아 있다.
> 기준일: 2026-06-26.

## Scope

302문항 전체 리더보드 갱신을 한 번에 밀지 않고, 후보 답안 생성과 Codex clean judge 배치 채점을 분리한다. 기존 `rag`는 law.go.kr DRF 조문 주입 중심이므로, 이번 milestone에서 말하는 RAG는 별도로 **authority_rag**로 부른다. authority_rag는 세무 문항은 tax/law MCP 또는 공식 법령 원문, 회계 문항은 K-IFRS MCP/로컬 기준서 DB로 실제 권위근거를 먼저 확인한 뒤 후보 모델에 제공하는 방식이다.

## Planning Gate

```yaml
planning_gate:
  team_validation_mode: manual-pass
  spec_delta: "ROADMAP에 302 재평가 운영 milestone을 active로 추가하고, 기존 302 계획을 batched Codex candidate + Codex clean judge 방식으로 구체화한다."
  perspectives:
    product: "101문항 기준 점수를 302문항 기준 최신 리더보드로 갱신해 공개 결과물의 신뢰도를 높인다."
    architecture: "candidate generation과 judge를 분리한다. 현행 per-answer judge 경로는 쓰지 않고 Codex clean judge용 batch judge pack을 만든다."
    security: "MCP/API credential 값은 문서화하지 않는다. 후보 실행은 기존 sandbox isolation 원칙을 유지한다."
    qa: "20문항 smoke -> 100문항 chunk -> 302 full merge 순서로 run/judge/error/leaderboard 누수 게이트를 통과시킨다."
    skeptic: "authority_rag를 구현하지 않고 기존 rag를 쓰면 사용자가 의도한 K-IFRS/tax MCP grounded RAG가 아니므로 결과 해석이 오염된다."
  dod:
    - "20문항 smoke에서 closed_book 후보 JSONL, authority pack, Codex clean judge pack, merge 결과가 모두 schema/aggregate 검증을 통과한다."
    - "100문항 단위 chunk 3개가 judge_error 없이 집계된다."
    - "leaderboard payload build가 holdout/private answer 누수 0으로 통과한다."
```

## Step Tree

- [x] Step 1 — Smoke boundary freeze: 20문항 샘플, 모델, 모드, 산출 경로를 고정하고 dry run 명령을 문서화한다.
  - AC: `docs/plans/302-reeval-plan-2026-06-24.md`와 이 문서가 서로 충돌하지 않고, 실행 범위가 `20 -> 100 -> 102`로 명시된다.
- [x] Step 2 — Candidate generation path: Codex 로컬 후보 생성은 judge 없이 실행하고 raw answer JSONL을 보존한다.
  - AC: `run_eval.py` 또는 별도 wrapper가 `--judge` 없이 `gpt-5.5` closed_book 20문항을 생성하고 `validate/run summary`가 error 0을 보고한다.
- [~] Step 3 — Authority RAG path: tax/law MCP + K-IFRS MCP/DB 기반 authority pack을 정의하고 기존 `rag`와 이름·해석을 분리한다.
  - AC: authority pack이 문항별 source id, 기준일, 인용 단위를 포함하고, accounting 문항은 K-IFRS 문단 인용을 가진다.
  - Progress: closed_book 평가용 authority pack 및 judge pack 생성 완료. 후보 생성 모드로서의 `authority_rag`는 아직 실행하지 않았다.
- [x] Step 4 — Codex clean judge pack: 후보 답안을 하나의 judge pack으로 묶고 clean judge session이 채점할 JSON 출력 계약을 고정한다.
  - AC: judge pack에는 question, rubric/gold summary, authority evidence, candidate answer, required JSON schema가 들어간다.
- [x] Step 5 — Merge and aggregate: batch judge output을 RunRecord/final 집계 포맷으로 병합한다.
  - AC: judge_error 0, code_grader dimension 유지, aggregate summary와 CI 스크립트가 실행 가능하다.
- [x] Step 6 — chunks: 후보 생성과 clean judge를 분리 반복한다.
  - AC: 각 chunk마다 candidate count, judge count, excluded/error count, elapsed, model/mode pin이 남는다.
- [~] Step 7 — Leaderboard refresh gate: full 302 결과로 leaderboard payload를 만들고 공개 반영 전 누수·버전핀·canary 게이트를 확인한다.
  - AC: holdout/private answer_text 누수 0, append-only version pin, public repo 반영 여부는 사용자 승인 대기.
  - Progress: `leaderboard/data/leaderboard-public.json` 생성 및 누수 가드 PASS, `npm run build` PASS. 공개 repo push는 기존 리더보드 데이터 대체/병합 정책 확정 전 보류.

## Execution Snapshot

- closed_book merged result: `outputs/reeval-302-20260626/gpt-5.5_closed_book_opus-merged-302.jsonl`
- Full 302: 302 records, judge_error 0, avg 91.94, grades A 219 / B 67 / C 13 / D 3.
- Holdout leaderboard payload: 253 records, avg 91.66, judge errors 0.
- Public sample payload: 49 records, avg 93.42, judge errors 0.
- Build gate: `leaderboard` static export PASS with `PAGES_BASE_PATH=/ktaxbench-leaderboard`.

## Defaults

- First candidate model: `gpt-5.5`.
- First modes: `closed_book` first, `authority_rag` second. 기존 `rag`는 비교 baseline으로만 유지한다.
- Chunking: smoke 20, then 100, 100, 102.
- Workers: local Codex candidate generation은 `--workers 4`에서 시작하고 smoke 결과로 6까지 올린다.
- Judge: Codex clean session batch judge. 현행 `--judge ...` per-answer subprocess 경로는 이번 milestone의 기본 경로가 아니다. Claude/Opus judge는 사용자 명시 승인 없이는 호출하지 않는다.
- Public update: private 결과 검증 후 별도 사용자 승인.

## Stop Conditions

- authority_rag pack이 세무/회계 권위 출처를 구분하지 못하면 full 302 실행 금지.
- judge JSON schema가 20문항 smoke에서 1건이라도 깨지면 100문항 chunk로 확대 금지.
- leaderboard build에서 holdout/private answer 누수 또는 stale public data overwrite 위험이 감지되면 공개 repo 반영 금지.

## Evidence Targets

- `playbooks/302-reeval-batched-authority.md`
- `outputs/reeval-302-<date>/chunk-*/`
- `outputs/reeval-302-<date>/judge-packs/`
- `outputs/reeval-302-<date>/JUDGMENT.md`
- `leaderboard/data/leaderboard-public.json`
