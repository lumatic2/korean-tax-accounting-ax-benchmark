# K-TaxBench

K-TaxBench is a Korean accounting and tax benchmark for evaluating whether an AI system can pass practical verification, not just produce fluent answers.

It combines domain-specific question design, statute/K-IFRS grounding, deterministic citation and calculation checks, LLM-judge rubrics, and a public leaderboard policy that separates practice data from the private ranking holdout.

**Live:** [tax-benchmark.askewly.com](https://tax-benchmark.askewly.com)  
**Public sample:** [data/sample-questions-v0.1.jsonl](data/sample-questions-v0.1.jsonl)  
**Technical report:** [docs/m4-tech-report-en.md](docs/m4-tech-report-en.md)

## Why This Exists

Accounting and tax AI fails in ways generic benchmarks do not measure well: fake legal citations, stale statute assumptions, wrong tax calculations, overconfident risk advice, and tool-use claims that were never actually grounded in retrieved authority.

K-TaxBench turns those failure modes into an evaluation harness for Korean VAT, corporate tax, income tax, basic tax law, accounting, and mixed agent workflows.

## What I Built

- A structured Korean accounting/tax benchmark schema with public/private visibility routing
- A Python evaluation runner for `closed_book`, `rag`, `agent`, and `agent_forced` modes
- Deterministic graders for multiple-choice, calculations, statute citations, and K-IFRS standard-paragraph references
- LLM-judge integration with explicit judge-failure handling and aggregation safeguards
- A public-safe leaderboard payload and static Next.js leaderboard UI
- A release pipeline that blocks private holdout leakage into public sample bundles

## What It Tests

- Korean VAT, corporate tax, income tax, basic tax law, accounting, and mixed workflows
- Citation accuracy against statutes and K-IFRS paragraph references
- Calculation and tax adjustment reasoning
- Risk analysis and practical communication
- Tool-grounded agent behavior, including whether cited authority was actually fetched

## Current Public State

- Public sample data: [data/sample-questions-v0.1.jsonl](data/sample-questions-v0.1.jsonl)
- Public sample rows in this repository: 43 `public_sample` questions
- Official release bundle: [leaderboard/public/data/public/release.jsonl](leaderboard/public/data/public/release.jsonl)
- Private holdout questions are intentionally not tracked in the public repository
- Leaderboard ranking is based on private holdout aggregates; holdout question text, answers, and ids are not exposed

The tracked data file is for reproduction, debugging, and portfolio review. It is not the ranking holdout.

## Architecture

```text
src/ktaxbench/
  loader.py              # JSONL question loading and filtering
  prompts.py             # closed_book / rag / agent prompt builders
  runner.py              # model execution and run record creation
  grading/               # deterministic graders + LLM judge integration
  report.py              # aggregate reports and public leaderboard payload

data/
  sample-questions-v0.1.jsonl   # tracked public sample only

leaderboard/
  app/                   # static public leaderboard UI
  data/                  # public-safe aggregate payload
  public/data/public/    # public sample release bundle

docs/
  adr/                   # design decisions
  findings/              # evaluation findings
  benchmark-schema.md    # question schema
  rubric-v0.1.md         # scoring rubric
```

## Quickstart

```bash
uv sync --extra dev
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
uv run pytest
uv run python scripts/run_eval.py --models claude-haiku-4-5 --modes closed_book --limit 5
```

The default tracked sample is public-safe. Private holdout runs are maintained outside this public repository.

## Reproduce The Public Release Bundle

```bash
uv run python scripts/package_release.py \
  --data data/sample-questions-v0.1.jsonl \
  --out dist/public-release-v1.0 \
  --version 1.0 \
  --accessed-at 2026-06-14 \
  --seed 42
```

The release gate blocks non-`public_sample` rows and rows without public release permission.

## Key Design Decisions

- Ranking uses private holdout aggregates only: [ADR 0009](docs/adr/0009-leaderboard-submission-policy.md)
- Agent evaluation is isolated from repository-local prompts and MCP state: [ADR 0008](docs/adr/0008-agent-eval-isolation.md)
- Citation grading supports both legal articles and K-IFRS standard-paragraph references: [ADR 0007](docs/adr/0007-citation-grader.md)
- Public sample scope and canary strategy are documented in [docs/m4-public-sample-scope.md](docs/m4-public-sample-scope.md)

## Public/Private Boundary

This repository is the public portfolio snapshot. It contains code, documentation, aggregate leaderboard payloads, and public sample data only. The private operating repository keeps the full holdout set and raw model outputs.

Boundary checks used for this snapshot:

```bash
git ls-files | rg "^(data/private/|outputs/|CLAUDE\.local\.md)"
rg -n -i "(api[_-]?key|secret|token|password|bearer|sk-[A-Za-z0-9]|ghp_|github_pat_|ANTHROPIC_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|DATABASE_URL)" --glob "!.git/**" --glob "!.venv/**" --glob "!uv.lock"
```
