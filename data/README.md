# Data Boundary

Tracked data in this directory is public-safe.

## Tracked

- `sample-questions-v0.1.jsonl` - public sample questions only.
- Every row must have `visibility: "public_sample"`.
- This file is for reproduction, debugging, demos, and portfolio review.

## Not Tracked

- `data/private/` - local-only full benchmark and holdout datasets.
- `outputs/` - local run logs and model answers.

The private holdout set is the ranking basis for the leaderboard, but holdout question text, answers, and ids must not be committed to the public repository.

## Checks

```bash
uv run python scripts/validate_questions.py data/sample-questions-v0.1.jsonl
python -c "import json; rows=[json.loads(l) for l in open('data/sample-questions-v0.1.jsonl',encoding='utf-8') if l.strip()]; print(len(rows), {r.get('visibility') for r in rows})"
```
