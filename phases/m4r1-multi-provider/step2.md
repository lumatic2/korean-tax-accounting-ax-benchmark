# Step 2: provider-smoke  ★ billing 게이트① (구독 소모)

> **라이브 CLI 호출 = 구독 소모.** 진입 전 사용자 opt-in 필수. 각 신규 provider 를 1문항으로 smoke 해 어댑터가 실제로 깨끗한 답을 뽑는지 확인 — 101문항 풀런 전 최소비용 검증.

## 읽어야 할 파일
- `scripts/smoke_model.py` — 왜: 단일 모델 1콜 smoke 스크립트. `--model <name>` 으로 신규 provider 검증. 그대로 사용.
- `phases/m4r1-multi-provider/step1.md` 결과(step1 summary) — 왜: 확정된 모델 ID·격리 플래그·max_workers. smoke 대상 이름.
- `src/ktaxbench/models/codex_cli.py`·`gemini_cli.py` — 왜: smoke 실패 시 디버깅 지점(출력 파싱·격리 플래그).

## 작업
- `uv run python scripts/smoke_model.py --model <gpt-codex-name>` — text 비어있지 않고 "4" 포함, raw_meta.error 없음 확인.
- `uv run python scripts/smoke_model.py --model <gemini-name>` — 동일.
- 격리 sanity: 후보가 도구/웹/MCP 를 못 쓰는지(plan/read-only 가 실제로 막는지) smoke 출력에서 확인. 안 막히면 step1 격리 플래그로 복귀.
- 동시성 mini-check(선택): HANDOFF 가 병렬 허용이라 했으면 `--workers 2` 로 2문항 동시 호출해 충돌 없는지 1회 확인.

## Acceptance Criteria
```bash
uv run python scripts/smoke_model.py --model <gpt-codex-name>    # exit 0, text에 4
uv run python scripts/smoke_model.py --model <gemini-name>       # exit 0, text에 4
```

## 검증 절차
1. 두 smoke 모두 exit 0 + 비어있지 않은 답.
2. latency·raw_meta 를 step summary 에 기록(풀런 시간·동시성 추정 근거).
3. `index.json` step2 → `completed` + summary. 실패 시 `blocked`(인증/모델ID 문제면 사유 기록).

## 금지사항
- 사용자 opt-in 없이 라이브 호출 금지. 이유: billing.
- smoke 실패(빈답·error)인데 step3 풀런 진행 금지. 이유: 101문항 오염·구독 낭비.
