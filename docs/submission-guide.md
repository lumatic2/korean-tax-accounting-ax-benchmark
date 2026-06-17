# K-TaxBench External Model Guide

이 문서는 외부 사용자가 K-TaxBench로 본인 LLM, RAG system, agent를 시험하는 방법을 정리합니다.

## 두 가지 사용 방식

### 1. 공개 샘플 self-test

public repository만으로 바로 실행할 수 있는 경로입니다.

- 목적: 모델 개발, prompt/RAG debugging, 포트폴리오 검토, 재현 테스트
- 데이터: `data/sample-questions-v0.1.jsonl`
- 결과: 로컬 점수와 리포트
- 제한: 공개 샘플이므로 공식 leaderboard 순위로 사용하지 않습니다.

```bash
git clone https://github.com/lumatic2/korean-tax-accounting-ax-benchmark.git
cd korean-tax-accounting-ax-benchmark

uv sync --extra dev
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
uv run python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book --limit 5
uv run python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
```

### 2. 공식 leaderboard submission

공식 순위는 private holdout으로만 산정합니다.

- 제출자는 model id, provider, mode, prompt/scaffold version, 실행 조건을 고정합니다.
- maintainer가 동일 실행기와 private holdout으로 재현 채점합니다.
- public repo에는 aggregate score, model metadata, submission policy만 공개합니다.
- holdout question text, answer key, ids, raw outputs는 공개하지 않습니다.
- 같은 모델의 재제출은 기존 행을 덮어쓰지 않고 새 submission row로 추가합니다.

초기 운영은 self-service가 아니라 maintainer-mediated submission입니다. 제출 자동화는 후속 작업입니다.

## 내 모델을 연결하는 방법

현재 실행기는 `config/models.yaml`의 model name을 받아 `scripts/run_eval.py`로 평가합니다.

```bash
uv run python scripts/run_eval.py \
  --models your-model-name \
  --modes closed_book,rag \
  --data data/sample-questions-v0.1.jsonl \
  --out outputs/results \
  --judge claude-sonnet-4-6 \
  --workers 4
```

### 지원되는 provider 경로

`config/models.yaml`에서 provider를 지정합니다.

```yaml
models:
  your-openai-model:
    provider: openai
    model_id: gpt-5.4
    temperature: 0.0
    prompt_version: v1
```

현재 registry가 인식하는 provider는 다음과 같습니다.

| Provider | 경로 | 비고 |
|---|---|---|
| `claude_cli` | Claude CLI subprocess | maintainer 평가 기본 경로 |
| `codex_cli` | Codex CLI subprocess | CLI 인증 필요 |
| `gemini_cli` | Gemini CLI subprocess | R1 순위 제외 정책 참고 |
| `openai` | OpenAI Python SDK | `uv sync --extra providers`, `OPENAI_API_KEY` 필요 |
| `google` | Google Python SDK | `uv sync --extra providers`, Google API key 필요 |

custom endpoint, local vLLM, internal gateway를 쓰려면 `src/ktaxbench/models/base.py`의 `ModelClient` protocol에 맞는 adapter를 추가하고 `src/ktaxbench/models/registry.py`에 provider branch를 등록하면 됩니다.

## 평가 mode

| Mode | 의미 |
|---|---|
| `closed_book` | 모델이 문항만 보고 답합니다. |
| `rag` | retriever context를 붙여 답합니다. |
| `agent` | 도구 호출 loop를 허용합니다. |
| `agent_forced` | 최종 답변 전 권위 근거 도구 사용을 강제합니다. |

공식 순위에서는 mode, prompt version, scaffold, accessed date를 submission metadata로 고정합니다.

## 결과 파일

`scripts/run_eval.py`는 `outputs/results/<model>_<timestamp>.jsonl`을 생성합니다. 각 row는 대략 다음 필드를 가집니다.

```json
{
  "question_id": "sample-0001",
  "question_hash": "...",
  "model": "your-model-name",
  "mode": "closed_book",
  "prompt_version": "v1",
  "answer_text": "...",
  "code_scores": [],
  "judge": null,
  "final": {"total": 86.0, "grade": "A"},
  "scaffold": {"prompt_version": "v1", "judge_model": null, "retriever_used": false},
  "accessed_at": "2026-06-18",
  "error": null,
  "latency_s": 12.3,
  "domain": "vat",
  "task_type": "calculation"
}
```

리포트는 다음 명령으로 만들 수 있습니다.

```bash
uv run python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
uv run python scripts/make_report.py outputs/results/*.jsonl --json outputs/leaderboard.json
```

## 제출 시 필요한 정보

공식 leaderboard 등재를 요청할 때는 최소한 다음 정보를 고정해야 합니다.

- Model name and exact model id
- Provider and version
- Mode: `closed_book`, `rag`, `agent`, or `agent_forced`
- Prompt/scaffold version
- Retrieval/tool configuration, if any
- Accessed date for statute or K-IFRS context
- Whether the run used public sample only or maintainer-run private holdout

## 정책

- 공개 샘플 점수는 practice/debug score입니다.
- 공식 rank는 private holdout aggregate만 사용합니다.
- self-reported score는 공식 등재하지 않습니다.
- 제출은 append-only입니다. 오류 정정은 기존 행 삭제가 아니라 superseding row로 처리합니다.
- 자세한 정책은 [ADR 0009](adr/0009-leaderboard-submission-policy.md)를 따릅니다.

---

# English

This guide explains how external users can evaluate their own LLM, RAG system, or agent with K-TaxBench.

## Two Usage Paths

### 1. Public sample self-test

This path works with the public repository only.

- Purpose: model development, prompt/RAG debugging, portfolio review, reproducibility checks
- Data: `data/sample-questions-v0.1.jsonl`
- Output: local scores and reports
- Limitation: public sample scores are not official leaderboard rankings

```bash
git clone https://github.com/lumatic2/korean-tax-accounting-ax-benchmark.git
cd korean-tax-accounting-ax-benchmark

uv sync --extra dev
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
uv run python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book --limit 5
uv run python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
```

### 2. Official leaderboard submission

Official rankings are computed on the private holdout only.

- Submitter freezes model id, provider, mode, prompt/scaffold version, and run conditions.
- The maintainer reproduces the run with the same harness and private holdout.
- The public repository exposes aggregate scores and policy metadata only.
- Holdout question text, answer keys, ids, and raw outputs are not exposed.
- Resubmissions create new rows instead of overwriting older rows.

Initial operation is maintainer-mediated, not self-service. Submission automation is future work.

## Connecting Your Model

The runner reads model names from `config/models.yaml`.

```bash
uv run python scripts/run_eval.py \
  --models your-model-name \
  --modes closed_book,rag \
  --data data/sample-questions-v0.1.jsonl \
  --out outputs/results \
  --judge claude-sonnet-4-6 \
  --workers 4
```

Supported provider branches are `claude_cli`, `codex_cli`, `gemini_cli`, `openai`, and `google`.

For a custom endpoint, local vLLM, or internal gateway, implement the `ModelClient` protocol in `src/ktaxbench/models/base.py` and register a provider branch in `src/ktaxbench/models/registry.py`.

## Reporting Results

```bash
uv run python scripts/make_report.py outputs/results/*.jsonl --out outputs/report.md
uv run python scripts/make_report.py outputs/results/*.jsonl --json outputs/leaderboard.json
```

## Required Submission Metadata

- Model name and exact model id
- Provider and version
- Mode: `closed_book`, `rag`, `agent`, or `agent_forced`
- Prompt/scaffold version
- Retrieval/tool configuration, if any
- Accessed date for statute or K-IFRS context
- Whether the run used public sample only or maintainer-run private holdout

## Policy

- Public sample scores are practice/debug scores.
- Official rank uses private holdout aggregates only.
- Self-reported scores are not listed as official results.
- Submissions are append-only.
- See [ADR 0009](adr/0009-leaderboard-submission-policy.md) for the full policy.
