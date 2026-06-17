# Step 4: live-resmoke-and-docs

## 읽어야 할 파일
- docs/findings/agent-tool-forcing.md ("후속 스모크" 섹션 — 갱신 대상)
- docs/adr/0008-agent-eval-isolation.md (완료)
- 스모크 출력 outputs/agentforced-isolation-smoke/*.jsonl

## 작업
격리 러너로 오염을 보였던 agent_forced 문항 재스모크(opus, judge=sonnet, DRF env 로드):
```bash
set -a && . ~/projects/tax-agent/.env; set +a
PYTHONPATH=src python -X utf8 scripts/run_eval.py --models claude-opus-4-8 \
  --modes agent_forced --id ktb-vat-0017,ktb-mixed-0002 --judge claude-sonnet-4-6 \
  --out outputs/agentforced-isolation-smoke --accessed-at 2026-06-09 --workers 2
```
finding "후속 스모크" 섹션에 격리 전/후 대비표 추가(ADR 0008 결과).

## Acceptance Criteria (3 게이트)
1. 후보가 "검증 리포트/문항 검증자"로 프레이밍하지 않음(answer_text 가 블라인드 에이전트 답).
2. agent_steps 에 ReAct [도구] 호출 포착(필요 문항 n_tool≥1).
3. forced_tool_unmet 오탐 해소(실제 미사용일 때만 점화).

## 금지사항
- 격리 전 오염 run 과 점수 직접 비교 금지(환경 다름). 행태(프레이밍·도구포착)만 대비.
- 스모크 결과가 게이트 미충족이면 finding 에 정직 기록 + 후속(예: --disallowedTools) 제안. 통과로 포장 금지.
