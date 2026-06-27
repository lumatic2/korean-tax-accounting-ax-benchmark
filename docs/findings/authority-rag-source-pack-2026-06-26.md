# Authority RAG source pack coverage

> Date: 2026-06-26.
> Contract: [ADR 0013](../adr/0013-authority-rag-mode-contract.md), `authority_rag-v1`.

## Summary

`authority_rag` source-pack filling is implemented and smoke-tested. After source sufficiency augmentation, the full 302-question locator pack now resolves to:

- 302 / 302 generation-ready questions.
- 875 / 883 source entries with `source_text_status=provided`.
- 6 entries are `optional_unresolved` authoring notes and 2 entries are non-authoritative secondary notes; neither blocks generation-ready status.
- Full 302-question pack passes the `authority_rag-v1` contract.

Generated artifacts, all gitignored:

- `outputs/reeval-302-20260626/authority-rag-contract-v1/manifest-302-authority-rag.json`
- `outputs/reeval-302-20260626/authority-rag-contract-v1/authority-pack-302-locator.json`
- `outputs/reeval-302-20260626/authority-rag-contract-v1/authority-pack-302-filled.json`
- `outputs/reeval-302-20260626/authority-rag-contract-v1/authority-pack-302-ready.json`
- `outputs/reeval-302-20260626/authority-rag-contract-v1/manifest-302-authority-rag-ready.json`
- `outputs/reeval-302-20260626/authority-rag-contract-v1/authority-pack-0-not-ready.json`

## Ready Set

Domain distribution for the 302 ready questions:

| domain | n |
|---|---:|
| vat | 68 |
| corp_tax | 66 |
| income_tax | 54 |
| accounting | 48 |
| basic_tax_law | 36 |
| mixed | 30 |

Task-type distribution:

| task_type | n |
|---|---:|
| citation | 81 |
| case_reasoning | 75 |
| calculation | 54 |
| risk_analysis | 54 |
| agent_workflow | 36 |
| multiple_choice | 1 |
| short_answer | 1 |

## Sufficiency Augmentations

The first 296-ready pass was generation-ready but not always sufficient. In a smoke run, `ktb-vat-0003` received VAT Act §61 and §69, but not Enforcement Decree §109, so the model correctly said the exact simplified-taxation threshold needed subordinate authority. The fix is `config/authority-pack-augmentations.json`.

Current augmentation policy:

| trigger | added authority |
|---|---|
| VAT Act §61 | VAT Enforcement Decree §109, for the KRW 104 million simplified-taxation threshold |
| VAT Act §63 | VAT Enforcement Decree §111, for simplified taxpayer value-added ratios |
| VAT Act §69 | VAT Enforcement Decree §114, for simplified taxpayer filing/payment procedure context |
| vague seed questions `ktb-vat-0001`, `ktb-corp-tax-0001`, `ktb-income-tax-0001`, `ktb-income-tax-0002`, `ktb-accounting-0001` | concrete statute/K-IFRS paragraph locators |

Authoring-note locators such as `관련 조문`, `관련 기준`, and `검색 필요` are treated as optional unresolved notes. They are visible as metadata but do not block generation-ready status when concrete augmented authorities are present.

## Verification

Commands run:

```powershell
$env:PYTHONPATH='src'; uv run pytest
$env:PYTHONPATH='src'; uv run pytest tests\test_reeval_batch.py
$env:PYTHONPATH='src'; uv run python scripts\prepare_reeval_batch.py validate-authority-pack --authority-pack outputs\reeval-302-20260626\authority-rag-contract-v1\authority-pack-302-ready.json
```

Results:

- `uv run pytest`: 144 passed.
- `tests\test_reeval_batch.py`: PASS as part of full suite.
- ready-only authority pack validation: PASS, 302 items.
- `ktb-vat-0003` smoke: answer now cites VAT Enforcement Decree §109 for the KRW 104 million threshold.

Additional sufficiency check after the 20-question `authority_rag` judge smoke:

- `ktb-basic-tax-law-0001` exposed an extractor gap: DRF law JSON `목내용` under `항 > 호 > 목` was not included, so Basic Tax Law §48(2)(2)(a) 1-month / 50% late-filing reduction was invisible to the model.
- The law-article extractor now recursively includes `항내용`, `호내용`, and `목내용`; authority pack enrichment also refreshes parseable law excerpts even when an older excerpt already exists.
- Regenerated pack: 302 / 302 generation-ready, contract PASS.
- Targeted rejudge: `ktb-basic-tax-law-0001` improved from 82/B in the smoke run to 96/A with the refreshed source pack.

20-question rerun with the refreshed pack:

- Output: `outputs/reeval-302-20260626/authority-rag-smoke20-rerun/gpt-5.5_20260626T095856Z.jsonl`.
- Result: 20 / 20 ok, average 94.05, grades A=19 / C=1.
- `ktb-basic-tax-law-0001` improved to 95/A in the rerun.
- `ktb-corp-tax-0004`, `ktb-mixed-0002`, and the other earlier B/C rows improved to A.
- Remaining C: `ktb-mixed-0003` at 64/C. The source pack contains VAT Act §39(1)(6), VAT Enforcement Decree §79, Corporate Tax Act §21(1), Corporate Tax Enforcement Decree §22(1)(2), and Corporate Tax Act §25(2). Judge memo identifies a model reasoning miss: the answer treated the KRW 500,000 non-creditable input VAT as deductible, but failed to add it to the KRW 5,000,000 entertainment expense base for Corporate Tax Act §25 limitation testing. Classification: model failure, not current source-pack insufficiency.

Full 302-question run:

- Output: `outputs/reeval-302-20260626/authority-rag-full302-gpt55/gpt-5.5_20260626T101847Z.jsonl`.
- Candidate generation: 302 / 302 ok, no run errors.
- Runner raw average: 90.22. This includes judge-failed rows as zero/code-only finals and should not be used as the leaderboard mean.
- Scored aggregate after excluding `judge_failed` rows: 289 / 302 scored, average 93.62, grades A=244 / B=30 / C=11 / D=4.
- Historical Opus judge failure: 13 / 302, all in `ktb-mixed-0018` through `ktb-mixed-0030`. A targeted 13-row rerun reproduced empty/non-JSON Opus judge responses. This is now classified as a judge execution/usage-path failure, not as unscored model output.

Codex clean judge rerun:

- Rule change: Claude/Opus judge calls are no longer executed without explicit user approval. The active judge path is Codex clean session: `codex exec --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check -C C:/ktaxbench-sandbox`.
- Judge model: `gpt-5.4` clean session, output pin `codex-clean-judge:gpt-5.4`.
- Judge pack: `outputs/reeval-302-20260626/authority-rag-full302-gpt55-codex-judge/codex-judge-pack-302.json`.
- Judgment output: `outputs/reeval-302-20260626/authority-rag-full302-gpt55-codex-judge/codex-judgments.jsonl`.
- Merged result: `outputs/reeval-302-20260626/authority-rag-full302-gpt55-codex-judge/gpt-5.5_authority-rag_codex-judge-merged-302.jsonl`.
- Result: 302 / 302 scored, judge_error 0, average 94.26, grades A=249 / B=35 / C=10 / D=8.
- Public-safe payload: `leaderboard/data/authority-rag-public.json`, generated as a separate `authority_rag` view; not averaged with `closed_book`.

Scored domain averages:

| domain | n scored | avg | grade distribution |
|---|---:|---:|---|
| accounting | 48 | 95.24 | A=43 / B=4 / D=1 |
| basic_tax_law | 36 | 96.69 | A=33 / B=3 |
| corp_tax | 66 | 92.28 | A=54 / B=5 / C=6 / D=1 |
| income_tax | 54 | 93.06 | A=45 / B=6 / C=1 / D=2 |
| mixed | 17 | 84.65 | A=8 / B=5 / C=4 |
| vat | 68 | 94.84 | A=61 / B=7 |

Lowest scored rows for follow-up triage:

| question_id | domain | task_type | score | grade | flags |
|---|---|---|---:|---|---|
| ktb-income-tax-0046 | income_tax | case_reasoning | 45.00 | D | assert_without_source |
| ktb-income-tax-0049 | income_tax | risk_analysis | 49.00 | D | fake_source |
| ktb-accounting-0039 | accounting | calculation | 49.91 | D | - |
| ktb-corp-tax-0045 | corp_tax | calculation | 59.00 | D | ignore_time_basis |
| ktb-mixed-0008 | mixed | citation | 63.00 | C | unverified_citation |
| ktb-corp-tax-0035 | corp_tax | case_reasoning | 64.00 | C | assert_without_source |
| ktb-corp-tax-0041 | corp_tax | case_reasoning | 66.00 | C | fake_source |
| ktb-income-tax-0043 | income_tax | case_reasoning | 68.00 | C | - |
| ktb-mixed-0011 | mixed | agent_workflow | 68.00 | C | - |
| ktb-corp-tax-0042 | corp_tax | case_reasoning | 70.00 | C | - |

## Next Step

`authority_rag` is now published on the public leaderboard as a separate view under the frozen `authority-pack-302-ready.json` and Codex clean judge path. It is non-ranking only in the narrow sense that it is not averaged into the official `closed_book` ranking until the mode contract is promoted to ranking-eligible.
