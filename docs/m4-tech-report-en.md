# K-TaxBench: A Multi-Dimensional Reliability Benchmark for Korean Tax and Accounting AI

**Yusung Jun** (Independent Researcher)

**Public materials:** Leaderboard — https://tax-benchmark.askewly.com
**Status:** Early-phase (phase-1) infrastructure report; external expert review and multi-provider evaluation forthcoming (§7).
**Note:** This is an English preprint draft (v0.1) translated and restructured from the Korean technical report. All figures are quoted from the project's internal evaluation findings and are not recomputed here. Internal design records (ADRs) and per-run findings referenced below are maintained in the project repository; the public sample and leaderboard are the externally reproducible artifacts (§8, Supplementary Materials).

---

## Abstract

AI systems are increasingly deployed in tax and accounting work, yet there is no reproducible standard for measuring whether such a system *can actually perform Korean tax law and accounting standards*. General LLM benchmarks and professional-exam accuracy measure whether a model "sounds plausible," not whether it "passes professional verification." A single accuracy number cannot separate the cases where the conclusion is right but the cited basis is wrong; the calculation is right but the practical advice is dangerous; the statute is found but misapplied to the facts; the amended law is not reflected; or an uncertain matter is asserted as settled.

K-TaxBench is an evaluation infrastructure that decomposes these five failure modes and measures them separately. It decomposes Korean tax and accounting practice into 6 domains × 7 task types (currently 302 items; the results in this report were measured on the initial v0.1 101-item set), and scores them with a multi-dimensional rubric of **accuracy, grounding, practicality, risk-awareness, and tool-use**. Scoring combines deterministic code-based grading (multiple choice, calculation, and citation-locator matching) with an LLM-judge (a 7-dimension rubric). To prevent a model from grading its own answers, the judge is fixed to a model outside the candidate pool, and the candidate and judge execution environments are isolated.

Key results: (1) Across three models (claude-opus-4-8 / sonnet-4-6 / haiku-4-5), a **discrimination spread of 40.2 points** was observed (over 118 commonly-solved pairs). (2) A RAG mode that injects primary statutory text raised the mean by **+8.6 points** over closed-book, and much of that gain came from a reduction in fabricated sources (hallucinations) — in citation-type items, `fake_source` flags fell from 14 to 4 (−71%). (3) Tool-use can only be measured reliably under "enforcement + grounding matching": weaker models did not call tools even under a forced gate and instead fabricated citations, and only code-level grounding comparison caught this.

**Scope and strength (important).** This is not a finished standard benchmark but an **early-phase (phase-1) evaluation-infrastructure report**. The first-phase scope is limited to discriminating three Claude-family models (cross-provider discrimination is future work), and the judge is also a Claude-family model (outside the candidate pool) — so the discrimination and self-evaluation-prevention claims should be read at the level of *within-family* comparison. The reported figures are **point estimates without confidence intervals or significance testing, and conclusions are bounded to "directional"** (§7). The core findings, gold answers, and holdout are part of the private validation set, so external direct reproduction is limited (public reproduction scope in §8).

---

## 1. Motivation — "Practical Reliability," Not "Accuracy"

### 1.1 The Problem

AI for tax and accounting is proliferating, but the market lacks a standard that answers the following questions:

- Does this AI actually understand Korean tax law and accounting standards?
- Does it avoid errors in calculation and tax adjustments?
- Does it correctly find and cite statutes, administrative rulings, court precedents, and tax-tribunal decisions?
- Does it avoid dangerous assertions and hallucinations?
- Does it answer in a form a licensed tax accountant or CPA can review?

General LLM benchmarks and exam-pass rates struggle to answer these. In tax and accounting practice, the catastrophic error is not the "wrong answer" but the **plausible-but-unverified answer**. A single accuracy number cannot distinguish the following five cases:

1. The conclusion is right but the **cited basis is wrong**.
2. The calculation is right but the **practical advice is dangerous**.
3. The statute is found but **misapplied to the facts**.
4. **The latest amended tax law is not reflected**.
5. An uncertain matter is **asserted as settled**.

### 1.2 The Five Axes — What We Measure

K-TaxBench decomposes a generated answer along five axes:

| Axis | Question |
|---|---|
| **Accuracy** | Is the conclusion and calculation correct? |
| **Grounding** | Are the cited statutes, standards, rulings, and precedents correct? |
| **Practicality** | Is the answer usable in a real work context? |
| **Risk-awareness** | Does it distinguish uncertainty, items requiring further confirmation, and risk conditions? |
| **Tool-use** | Do RAG/Agent modes actually perform retrieval and verification? |

The core message compresses to one line: we need **"passed verification," not "speaks well."**

### 1.3 Borrowing Design Principles from the Accounting Conceptual Framework

The intellectual starting point of this benchmark is the observation that accounting has *already* defined the conditions for "reliable information" — the **qualitative characteristics** of the *Conceptual Framework for Financial Reporting*. We demand of AI-evaluation information the same qualitative characteristics that financial information must satisfy. This borrowing is **design inspiration**, not a claim that the mapping below is empirically established — in particular, **construct validity (a one-point score difference equals one unit more trustworthy in practice) is currently a *hypothesis/goal*, and its empirical validation (expert usefulness ranking, inter-rater agreement, etc.) is placed on the roadmap in §7**:

- **Relevance** (CF 2.6) → **construct validity**. A one-point difference in score must mean "one unit more trustworthy to delegate in practice." A high multiple-choice accuracy does not mean a model can be trusted with tax adjustments.
- **Faithful representation** (2.12) → **expert-reviewed gold answers** (target state). A gold answer must faithfully represent the substance of the statute or standard. A benchmark whose answers are wrong is not a measurement instrument but a source of contamination. Every gold answer carries a **time-basis stamp**. *Current state:* the public 34 items have completed **author self-review** (2026-06-12) and the holdout is at the internal-review stage — "expert-reviewed gold answers" is the *target*, with only items passing external expert review promoted to `version:1.0` (§7).
- **Comparability** (2.24) → **version pinning**. Models A and B must be measured under the same conditions. Mode, time basis, data version, and scaffold are recorded alongside the score.
- **Verifiability** (2.30) → **contamination resistance + deterministic-grading first**. Anyone grading must obtain the same score, and the score must be guaranteed to come from genuine ability rather than training leakage.
- **Timeliness** (2.33) → **point-in-time version management**. Tax law changes every year; last year's gold answer may be this year's error.
- **Understandability** (2.34) → **multi-dimensional diagnosis**. The consumer of the score is a decision-maker at an accounting firm. They need to see *where* the model is weak, not a single "total 78," to decide on adoption and improvement.

Three of these are the **load-bearing trio** that we always check first in any design decision: contamination resistance (verifiability), multi-dimensional scoring (understandability), and expert-reviewed gold answers (faithful representation). When designing a new item, scoring method, or feature, we first ask: "Does this strengthen or undermine these three axes?"

---

## 2. Benchmark Construction

### 2.1 Item Distribution

At the time of this report, the v0.1 item set contained 101 items (the benchmark has since expanded to 302 items across 6 domains — see README.md).

**By domain** — VAT 22 · corporate tax 22 · income tax 19 · accounting 16 · basic tax law 12 · mixed 10.

**By task type** — citation 27 · case-reasoning 23 · risk-analysis 20 · calculation 17 · agent-workflow 12 · multiple-choice 1 · short-answer 1.

Pure knowledge-recall items (MC and short-answer) are minimized to a basic-discrimination role only; practical validity is carried by case-reasoning, risk-analysis, and agent-workflow items. Calculation items are admitted only as "rule proxies" — only when the formula can be inverted and scored deterministically.

### 2.2 Schema — Contamination Tracking and Timeliness Baked into Items

Each item carries metadata for measurement reliability:

- **visibility** (`public_sample` / `holdout` / `private`) — separates the public sample from the private validation set (§2.3).
- **hash** — an item-content hash for tracking contamination and plagiarism.
- **time_basis** — pins, per item, the effective date of the statute the gold answer is based on. Because tax law is amended annually, an answer without a time basis violates faithful representation and timeliness.

### 2.3 Public 34 vs. Holdout Separation

The public-release set is derived deterministically by a whitelist rule — `visibility=public_sample` ∧ `public_release_allowed` ∧ `status ∈ {internal_reviewed, expert_reviewed}` = **34 items** (as of 2026-06-12).

Public-34 distribution: income tax 8 · accounting 7 · corporate tax 6 · VAT 5 · basic 5 · mixed 3 / citation 13 · calculation 7 · case 6 · risk 6 · MC 1 · short 1 / difficulty medium 31 · hard 1 · easy 2.

The design intent is explicit: **hard and expert items are concentrated in the holdout**. The public set is treated as "practice problems," assumed to become contaminated over time, and rotated periodically. Genuine discriminative power and timeliness are carried by the private validation set — this separation is the moat a competitor cannot replicate.

---

## 3. Methodology

### 3.1 Three Modes — closed-book / RAG / agent

The same item is run in three modes to decompose *the effect of tool-use on reliability*:

- **closed-book** — the model answers from internal knowledge only.
- **rag** — primary statutory text is injected via live retrieval from Korea's national law database (DRF API), then the model answers.
- **agent** — in a ReAct loop, the model itself calls tools to look up and verify.

Modes are never mixed in comparison; only like-mode is ranked against like-mode (comparability).

### 3.2 Multi-Dimensional Scoring — Code Grading + LLM-Judge

Scoring has two layers:

- **Code grading (deterministic)** — multiple-choice answers, calculation results (by formula inversion), and citation locators (whether the cited statute/standard paragraph matches the gold set) are scored programmatically. The rationale for scoring calculation as a "rule proxy," and for scoring citations at the granularity of K-IFRS paragraphs, is documented in the project's design records (ADRs).
- **LLM-judge (7-dimension rubric)** — conclusion accuracy, basis accuracy, calculation process, fact handling, uncertainty handling, practical usability, etc., are scored at the statement level with partial credit. This expresses "the conclusion is right but only part of the basis is correct" as a score.

Agent reliability is measured not by a single correct answer but by repeat consistency (pass^k).

### 3.3 Removing Self-Evaluation and Isolating the Environment

If the model under evaluation grades its own answer, a self-preference ceiling appears in the score. To prevent this, the **judge is always a model outside the candidate pool** (e.g., opus candidate → sonnet judge; sonnet candidate → opus judge).

A subtler contamination came from the *execution environment*. When the candidate model was run with `claude -p` inside the benchmark repository directory, the model read the repo's CLAUDE.md (judge rules, gates, rubric vocabulary) and re-framed itself as an "item verifier," or routed around the harness via a competing MCP in the environment (a national-law MCP) so that the evaluation harness failed to observe the tool call. The mitigation is to isolate the candidate and judge in an empty sandbox directory outside the repo and home, with `--strict-mcp-config`. After isolation, the *observed* verifier-framing and tool-false-positive paths were resolved on re-smoke — this is the mitigation of specific leakage paths observed in this harness, not a claim that all contamination is eliminated (remaining leakage paths in §7; §5.4).

### 3.4 Forced-Tool Mode — Authority Gate + Grounding Match

The free agent mode measures "does the model recognize that a tool is needed (judgment)," but "when forced, does it correctly call and integrate the right tool (execution capability)" is a separate axis. The latter is measured by a forced mode (`agent_forced`) that **gates on mandatory authority-tool use and code-compares whether the statute cited in the final answer was actually retrieved**. Because memory-citation and tool-grounded citation are textually indistinguishable, this code comparison is the entirety of tool-measurement reliability (§5.3).

### 3.5 Reproducibility — Version Pinning

Every score is recorded together with model id, data hash, scaffold, and mode. The lesson that comparisons become a lie unless the scaffold is fixed and recorded is already established by external benchmarks (e.g., SWE-bench).

---

## 4. Results

> The figures below are quoted from the 2026-06-11 M3 re-evaluation (101 items) and accompanying findings. They are not recomputed in this report.
>
> **Statistical strength (important).** The reported figures are **point estimates** without confidence intervals, repeated-run variance, or significance testing — the LLM-judge has run-to-run variance (§7) and small-n ablations are single runs. All conclusions are therefore bounded to "directional evidence" and no statistical significance is claimed. Confidence intervals and paired tests for the headline figures are future work (§7).

### 4.1 Three-Model Discrimination — spread 40.2

Means over the 118 (item × mode) pairs that opus, sonnet, and haiku all solved:

| Model | Mean |
|---|---|
| claude-opus-4-8 | **92.0** |
| claude-sonnet-4-6 | 86.3 |
| claude-haiku-4-5 | **51.7** |

→ **spread 40.2 points.** (Model means in the table are displayed rounded to one decimal; the spread of 40.2 is the difference of the *un-rounded* means — the 0.1 gap from the displayed arithmetic 92.0 − 51.7 = 40.3 is an artifact of rounded display.) This widened from 30.1 in the prior full report (2026-06-09, 81 records). The result of newly added hard income-tax items (capital-gains calculation, income classification, documentation risk) separating weaker models more sharply. A benchmark separating weak and strong models *more* sharply via new items is the opposite of a saturation signal — it means headroom remains.

### 4.2 RAG vs. closed-book — +8.6 (hallucination reduction, reproduced)

Three-model means over the common set:

| Mode | Mean |
|---|---|
| closed_book | 72.4 |
| rag | **81.0** |

→ RAG gives **+8.6 points.** The mechanism of this gain is revealed in a separate ablation. Comparing haiku (the tier where hallucination concentrates) on 8 citation items, closed-book vs. RAG, the `fake_source` flag — where the judge ruled that the model *generated a non-existent basis* — fell from **14 to 4 (−71%)**, and the mean total rose from 24.9 to 60.25. That is, RAG raises the score less by making the model "know more" and more by **suppressing fabricated-source generation**.

However, **RAG is not a panacea.** For statute-citation items where the answer *is* the statute (VAT, corporate-tax, income-tax provisions), the RAG gain is large (+52 to +89), but for National Basic Tax Act reasoning items where the answer is a judgment about just cause, procedure, or tribunal precedent, it actually declined (−9, −20). Injecting statutory text alone causes the model to anchor incorrectly on precedent- and procedure-type items — this type requires separate precedent retrieval. A counter-example was also reproduced in a new income-classification item (0017), where sonnet declined under RAG (closed 70 → rag 44). *Decomposing* the per-mode differences is a pattern consistent with the construct-validity hypothesis (it is not a direct demonstration that score maps to real-world usefulness — see the validation roadmap in §7).

### 4.3 "Forced Tool" ≠ "Retrievable Fact"

The hypothesis that "if an answer requires an external fact (a statute), the model will use a tool" was refuted. On an item asking about *well-known rules* — depreciation and mileage-log caps (corp-tax-0012) — all three models called tools 0 times; opus's answer was "all key provisions are confirmed, so additional tool calls are unnecessary." The true condition for tool-forcing is not "a retrievable fact" but **the model being genuinely unsure of that fact**. Famous caps are memorized, so strong models answer correctly and weak models answer incorrectly, both without tools. Relying on a model's voluntary tool use therefore makes measurement unstable — the tool-use axis must be measured in forced mode (§5.3).

### 4.4 The External-Verification Value of the Calculation Rule Proxy

Code grading (the calculation rule proxy) produced cases of external verification that break the self-evaluation ceiling. On a capital-gains item, the orchestrator corrected an asset-classification error (Income Tax Act Art. 104(1) item 11 → item 1); on a donation item, it caught a contradiction between the final value and the explanation. These are error types caught only by deterministic formula comparison, which model self-judgment misses.

### 4.5 New Income-Tax 7-Item Discrimination + Integrity

On the new income-tax items 0013–0019 (× 2 modes), the three models again sorted monotonically:

| Model | New-income mean |
|---|---|
| opus | **95.7** |
| sonnet | 89.7 |
| haiku | 73.8 |

On easy calculations (computed tax, gross-up), all three score ~100; but on case-reasoning (income classification) and risk (transfer documentation, financial-income determination), **haiku collapses to D-grade (29–48)** while opus holds 88–100. An important integrity signal: **zero cases of a uniform 0-point collapse (a data defect)** — the new items did not break gold integrity (noise check PASS).

---

## 5. The Live Validations That Built Measurement Reliability

For the results (§4) to mean anything, the measurement apparatus itself must be trustworthy. The following are records of validating that apparatus live.

### 5.1 RAG-Mode Normalization

The −71% in `fake_source` (§4.2) shows the RAG retrieval pipeline (live national-law DRF) working as intended.

### 5.2 Agent Runner in Production Operation

opus actually called the statute-lookup tool 4 times on mixed-0001 (VAT Act §39, §52; Corporate Tax Act §25), and the runner executed and reflected them via live DRF. A network drop occurred mid-run (WinError 10054), but the model succeeded by retrying on the next step — confirming graceful error handling and retry in the field.

### 5.3 The Forced Gate Is Not Fooled by Fabrication (Key)

Running a timeliness-trap item (corp-tax-0013, the 80% cap on carried-forward losses) in forced mode:

| Model | Actual tool calls | grounded | flags | Total |
|---|---|---|---|---|
| **opus** | **2 (statute lookup)** | Arts. 13, 14 | none | **99** |
| **haiku** | **0** | — | `forced_tool_unmet` (−15) | 78 |

Even with the gate raised, haiku **cited Article 13 verbatim and wrote "tool confirmation complete" — yet made 0 actual calls. Fabrication.** Its `agent_steps` were empty, so `authority_used=false`, and the grounding gate caught it. Had this code comparison not existed, haiku's memory-citation and opus's tool-grounded citation would have been textually indistinguishable — a live demonstration of the thesis that this comparison is the entirety of tool-measurement reliability.

This process also surfaced a bug that could not have been caught without live execution: the statute-lookup tool returned only the chapter title for a chapter-opening article (Art. 13), due to an encoding issue, so that "tool refused" and "tool broken" were contaminating the verdict. It was fixed together with a regression test.

### 5.4 Mitigating Harness Contamination via Environment Isolation

For the environment contamination described in §3.3, the *observed leakage paths* were resolved by isolation (`isolated=True`, sandbox cwd + `--strict-mcp-config`) on re-smoke. The 2 items that had shown contamination passed all three gates (verifier-framing gone / ReAct tool capture / `forced_tool_unmet` false-positive removed):

| Item | ReAct tool capture | grounding ratio | Total/Grade |
|---|---|---|---|
| ktb-vat-0017 | n=2 (VAT Act §61; Enf. Decree §109) | 1.0 | 92/A |
| ktb-mixed-0002 | n=4 (Income Tax Act §21; Enf. Decree §87, §129, etc.) | 0.75 | 88/B |

The answers also became honest — vat-0017 said "cannot be determined from the given data alone" (risk-awareness), and mixed-0002 distinguished "what was/was not confirmed by tools" and derived the correct answer (KRW 88,000).

---

## 6. Comparison with External Benchmarks

> Empirical survey as of 2026-06-12.

Adjacent benchmarks surveyed:

- **KMMLU-Pro** [1] — 2,822-item MCQA based on Korean national professional-license exams. The Tax & Accounting domain includes 238 certified-tax-accountant, 208 CPA, and 159 customs-broker items. Evaluation measures only answer accuracy plus official pass criteria (40% per subject, 60% average).
- **KBL** [2] — a Korean legal benchmark evaluating both closed-book and open-book (with a legal corpus); open-book improves accuracy by up to **+8.6%**.
- **LegalBench** [3] — 162 Anglo-American legal-reasoning tasks, expert-led design.
- **PLAT** [4] — targets Korean tax law but is narrow: a **binary classification** of penalty-tax legitimacy.

### Five Key Differentiators

1. **From multiple-choice accuracy to generative practical reliability.** The comparison benchmarks measure only MCQA/classification accuracy or pass/fail. K-TaxBench decomposes a generated answer along the five axes of accuracy, grounding, practicality, risk, and tool-use.
2. **Grounding-enforced grading.** Citation accuracy is code-graded at the statute/standard-paragraph level. None of the comparison benchmarks directly grade citation accuracy — detecting hallucinated/fabricated citations is the core of K-TaxBench.
3. **Timeliness.** Per-item `time_basis` + version pinning track amendments. KMMLU-Pro's "most-recent-year exam" is only a snapshot, not point-in-time version management.
4. **(Within the survey scope) the only generative, multi-dimensional Korean tax-and-accounting practice benchmark.** PLAT is narrow (penalty tax) and KMMLU-Pro tax/accounting is a multiple-choice license exam.
5. **Contamination resistance (canary) and self-evaluation prevention (non-self judge, isolation).** The comparison benchmarks do not address contamination tracking or self-evaluation guards.

Independent cross-check (directional): KBL also improved accuracy via open-book (retrieval) (+8.6 percentage points) — the effect of retrieval reducing hallucination and raising scores reproduces in the same direction on an independent Korean legal benchmark. (Our RAG gain of +8.6 points is numerically the same but in a different unit — accuracy percentage points vs. rubric score — so the coincidence is incidental and we attach no meaning to it.)

> **Limitation (important).** This is a comparison of *design and evaluation axes*, not of scores. The KBL/KMMLU figures are each paper's reported values and were not reproduced under the same models/conditions as K-TaxBench. All "first/only" claims are bounded to "within the 2026-06-12 survey scope."

---

## 7. Limitations and Future Work

- **Review stage.** A self-review round for the public 34 items is complete (2026-06-12; five-axis verification — accuracy, grounding, timeliness, internal consistency, rubric — against primary statutory and standard text). The next step is to introduce an external tax/accounting expert-review protocol; only items passing expert review are promoted to `version:1.0`.
- **Judge non-determinism.** The LLM-judge has run-to-run score variance. We correct with variance logging and expert spot-checks, and bound the conclusions of several findings to "directional" (small-n ablations are single runs).
- **Sample design.** Holdout operation, rotation, and per-domain confidence intervals are work in progress. Claiming per-domain confidence intervals requires growing the per-domain samples.
- **Multi-provider and single-family limitation.** The first-phase scope concentrated on discriminating three Claude-family models, and the judge is also a Claude-family model. Therefore (a) the discrimination spread is a *within-family* observation and cross-provider generalization is unvalidated, and (b) the non-self-judge safeguard is at the "same-family non-self" level, which does not fully exclude family-level preference bias (same-family preference). Cross-discrimination with GPT/Gemini plus judge-swap robustness is a key future task.
- **Statistical strength.** The headline figures (spread 40.2, RAG +8.6, etc.) are **point estimates** without confidence intervals, repeated-run variance, or significance testing. Conclusions are claimed only as "directional." Run-level variance logging, bootstrap CIs, and paired tests for the core figures are future work; until then we keep the strength of title-level claims correspondingly low.
- **Construct-validity evidence.** "One point = one unit of practical trust" is still a *hypothesis*. Validation roadmap: correlation between external experts' pairwise usefulness ranking and our score, inter-rater agreement, and correlation with actual work risk. The IFRS qualitative-characteristics borrowing is design inspiration; empirical validation of the mapping is placed on this roadmap (§1.3).
- **Reproducibility boundary.** The public track (public 34 + leaderboard + policy) is reproducible, but the core findings, holdout items, and internal design records are part of the private validation set, so external direct reproduction is limited. That is, this is not a "fully reproducible standard" but a **partially reproducible public track + private validation core**. The public/private reproduction scope and the minimal public-34 reproduction procedure are in §8.
- **Remaining leakage / contamination paths.** Isolation, canary, and non-self judging only mitigate *specific observed* leakage, not a complete solution. Remaining paths: (1) same-family judge preference bias; (2) model memorization of public statutes (correct without tools → bypassing tool-use measurement); (3) prompt-channel leakage; (4) public-set contamination before rotation; (5) canaries are inserted only at public release, so the prior period is uncovered. Monitoring and mitigation of each path are ongoing.

---

## 8. Reproducibility

> **Reproduction scope (important).** This benchmark is *partially reproducible*. **Publicly reproducible:** the public 34-item sample, the leaderboard, the submission policy, and the version-pinning convention. **Limited external reproduction:** the raw data of core findings (per-run logs), holdout items, gold answers, and internal design records (ADRs) are part of the private validation set (for the scoring-set moat and contamination prevention). The minimal reproduction procedure and expected outputs runnable from the public 34 alone accompany the public release.

- **Version pinning** — model id, data hash, scaffold, and mode are recorded with every score (§3.5).
- **Public-34 release** — derived by a deterministic whitelist; a canary (`KTAXBENCH-CANARY-<uuid>` + a global sentinel) is inserted only at the moment of public release. The canary is excluded from the hash basis, so item hashes remain invariant after insertion.
- **Leaderboard policy** — the four failure modes of the "Leaderboard Illusion" (retry best-pick, selective withdrawal concealment, access asymmetry, public-set overfitting) are blocked by five rules (frozen version pins, holdout ranking shown separately, no withdrawal — supersede only, reproduction-verified listing, identical public set). The public leaderboard enforces these via the UI (https://tax-benchmark.askewly.com).
- **Usage-budget lesson** — 101 × 2 modes × 3 models = 606 evaluations exceed a single 5-hour subscription session window. Pushing concurrency too high triggers server rate-limits and backfires; a single-process `--workers 6` with exponential-backoff retry is safe. A session usage limit cannot be overcome by retry, so the next full re-run splits the session window per model and runs sequentially.

---

## References

[1] S. Hong, S. Kim, G. Son, S. Kim, Y. Hong, and J. Lee, "From KMMLU-Redux to KMMLU-Pro: A Professional Korean Benchmark Suite for LLM Evaluation," arXiv:2507.08924, 2025.

[2] Y. Kim, Y. R. Choi, E. Choi, J. Choi, H. J. Park, and W. Hwang, "Developing a Pragmatic Benchmark for Assessing Korean Legal Language Understanding in Large Language Models," in *Findings of the Association for Computational Linguistics: EMNLP 2024*. arXiv:2410.08731.

[3] N. Guha, J. Nyarko, D. E. Ho, C. Ré, et al., "LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models," in *Advances in Neural Information Processing Systems (NeurIPS) Datasets and Benchmarks Track*, 2023. arXiv:2308.11462.

[4] E. Choi, Y. Suh, S. Lee, H. Oh, J. Kang, W. Hur, H. Park, and W. Hwang, "Taxation Perspectives from Large Language Models: A Case Study on Additional Tax Penalties," in *Proceedings of EACL 2026 (main conference)*. arXiv:2503.03444.

## Supplementary Materials

Per-item data, per-run findings, and architectural decision records (ADRs) for the design choices cited throughout (rule-proxy calculation grading, paragraph-level citation grading, agent ReAct loop, forced-tool mode, evaluation isolation, leaderboard policy) are maintained in the project's documentation. The externally reproducible artifacts are the public 34-item sample and the live leaderboard at https://tax-benchmark.askewly.com.
