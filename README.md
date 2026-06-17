# K-TaxBench

K-TaxBench is a Korean accounting and tax benchmark for testing whether an AI system can pass practical verification, not just produce fluent answers.

It evaluates Korean tax, accounting, and agent workflows across closed-book, RAG, and tool-using modes. The project is built around evidence-grounded questions, deterministic checks for citations/calculations, LLM-judge rubrics, and a public leaderboard policy that keeps ranking data separate from practice data.

Public leaderboard: [tax-benchmark.askewly.com](https://tax-benchmark.askewly.com)

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

The default tracked sample is public-safe. Private benchmark runs use an ignored local dataset under `data/private/`.

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

## Publication Boundary

This repository is prepared for public portfolio use only after the tracked tree contains no private holdout questions or local credentials. The working copy may still contain ignored private artifacts such as:

- `data/private/`
- `outputs/`
- `CLAUDE.local.md`
- local virtual environments and caches

Before changing GitHub visibility to public, run:

```bash
git ls-files | rg "^(data/private/|outputs/|CLAUDE\.local\.md)"
rg -n -i "(api[_-]?key|secret|token|password|bearer|sk-[A-Za-z0-9]|ghp_|github_pat_|ANTHROPIC_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|DATABASE_URL)" --glob "!.git/**" --glob "!.venv/**" --glob "!uv.lock"
```

If this repository already has private data in Git history, publish from a cleaned branch or a fresh public repository rather than simply flipping visibility.
