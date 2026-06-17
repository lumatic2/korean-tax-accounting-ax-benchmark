# Roadmap Gap Review

Date: 2026-06-18

## North Star
한국 회계·세무 AI가 "그럴듯하게 말하는가"가 아니라 "실무 검증을 통과했는가"를 재는 표준 평가 인프라.

Portfolio-facing goal: public readers should be able to understand K-TaxBench, reproduce the public sample path, and trust that private holdout assets are not exposed.

## Current State
- `ROADMAP.md` is a legacy roadmap without `harness:goal` / `harness:milestone` markers.
- `roadmap_sync.py status` reports 0 active milestones, so `/harness` must not infer a runnable target.
- GitHub repository visibility is currently PRIVATE.
- Public release assets exist in the leaderboard path, but the main tracked benchmark file mixes `public_sample` and `holdout` rows.
- Existing worktree is dirty before this run: `ROADMAP.md`, `leaderboard/app/globals.css`, `leaderboard/app/page.jsx`, plus empty untracked files named `'`, `Claude`, and `{rf}`.

## Gap
- Active harness milestones are exhausted.
- Compare the north star above with current evidence before starting new implementation.
- Do not infer completion without a new DoD and evidence path.
- Publication-readiness is not represented as a measurable harness milestone.
- The portfolio/publication cleanup has at least one security/data-boundary risk: holdout rows should not remain in a public-facing tracked sample artifact.

## Proposed Next Horizon
N1 - Publication-safe portfolio release
- Gap: Repository is private, but the user intends to publish it as a portfolio artifact after hiding sensitive data.
- DoD: README is public-facing, public data paths contain only release-safe rows, private/holdout assets are excluded or moved to ignored paths, and the repo passes a targeted secret/data-boundary scan.
- Evidence: `README.md`, `data/README.md`, public dataset manifest/count check, `rg` secret scan output, `git ls-files` boundary check, and test/validation command output.
- Recommended priority: P0.

N2 - External expert review operating track
- Gap: M7 is the current strategic bottleneck, but it is not encoded as an active harness milestone.
- DoD: expert review protocol, sample packet, reviewer tracking artifact, and at least one outreach-ready brief.
- Evidence: `phases/m4-public-track/step4` or a new review playbook, reviewer packet files, and status tracker.
- Recommended priority: P1 after publication-safe cleanup.

N3 - M8 expansion continuation
- Gap: ROADMAP says M8 expansion is in progress, but the active harness marker is absent.
- DoD: next bounded question-authoring batch with authority logs and validator/test pass.
- Evidence: `outputs/m8/.../run.json`, `tool-calls.jsonl`, `data/sample-questions-v0.1.jsonl`, validation output.
- Recommended priority: P2 unless the immediate goal is more benchmark depth rather than public portfolio readiness.

## Recommended Promotion
Promote N1 as the next active milestone:

```markdown
<!-- harness:milestone id="N1-publication-safe-portfolio-release" status="active" priority="P0" -->
### N1 — Publication-safe portfolio release
- DoD: README is public-facing; tracked public data contains only release-safe rows; private/holdout assets are excluded or moved to ignored paths; targeted secret/data-boundary scan passes; validation/test smoke passes.
- Evidence: `README.md`; `data/README.md`; public/holdout row-count check; `git ls-files` boundary check; `rg` secret scan; validator/test command output.
- Gap: The repo is still private, but publication would currently expose internal holdout rows and an internally oriented README.
- Status: [ ]
```

## Recommendation
Promote one proposed item to ROADMAP.md only after the user approves the next horizon.
