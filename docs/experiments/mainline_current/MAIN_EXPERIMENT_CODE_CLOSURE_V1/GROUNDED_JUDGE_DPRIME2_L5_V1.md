# Grounded-Support Judge v1 (LLM-judged paper-grounding)

- input jsonl: `outputs/results_main/review_infer/mainline_final_v1_flaw_fix_dprime2_9b_fulltest39_20260507.jsonl`
- paper-text source: `/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-test.arrow`
- judge model: `deepseek-v3-2-251201`
- n_papers: **35**

**Honest framing.** These rates are **LLM-judged**, not human-verified. The judge model itself can be wrong. Per `PAPER_GAP_REMEDIATION_PLAN.md` §B2 the follow-up step is a 30-sample human alignment pass to bound judge agreement. Until then, paper text must say *"LLM-judged paper-grounded rate"*, not *"human-verified grounding"*.

## Evidence (strong support, supports / partially_supports)

- total judged: **67**
- paper_grounded: **58**
- not_paper_grounded: 9
- parse_error: 0
- **Grounded_Support_Precision = 0.8657**

### By support source bucket

| bucket | total | grounded | rate |
|---|---:|---:|---:|
| `result_or_experiment` | 49 | 40 | 0.8163 |
| `method_or_approach` | 18 | 18 | 1.0000 |

## Flaws — three nested views

Flaw judgment is reported through three nested scopes so the paper narrative can match the metric to the audience:

1. **`raw`** — every flaw_candidate the system ever produced (worker outputs + fallback). 
   This is the upper bound on flaw output volume.
2. **`hygiene`** — flaws that survive `build_decision_hygiene_view` with `status ∈ {candidate, confirmed}`. This is what the reviewer actually sees in the final report.
3. **`hygiene_evidence_aware`** — `hygiene` plus rescued non-fallback flaws with at least one real-strong evidence anchor (`strength=strong`, `binding_status=bound_real_claim`, `stance != missing`). Schema-dump fallback flaws are never rescued.

| view | total | grounded | not_grounded | parse_err | **rate** |
|---|---:|---:|---:|---:|---:|
| `raw`                     | 62 | 38 | 24 | 0 | **0.6129** |
| `hygiene`                 | 40 | 25 | 15 | 0 | **0.6250** |
| `hygiene_evidence_aware`  | 44 | 27 | 17 | 0 | **0.6136** |

- fallback flaws (flaw-fallback*): 0 total, 0 grounded (rate = 0.0000)

### Evidence-aware rescue contributions

Flaws appearing in `hygiene_evidence_aware` but **not** in `hygiene` are entries that the relaxation rescued. Both correct rescues (`paper_grounded`) and bad rescues (`not_paper_grounded`) are listed so the net contribution of the rescue rule is auditable.

| paper_id / flaw_id | judgment | title | reason |
|---|---|---|---|
| `ye3NrNrYOY/flaw-2` | **paper_grounded** | Baseline comparison lacks methodological detail on 'fixed' components | The paper explicitly states which components are fixed and updated, but the flaw correctly notes that the mathematical definitions of the transition and mixing functions are not fully detailed in the  |
| `WpXq5n8yLb/flaw-2` | **paper_grounded** | Ambiguous Attribution of Speedup Source in TensorRT-LLM | The paper explicitly attributes the speedup to ReDrafter's mitigation of a memory bottleneck, but lacks evidence isolating its contribution from other TensorRT-LLM optimizations. |
| `TPAj63ax4Y/flaw-1` | **not_paper_grounded** | Lack of Grounded Evidence for Technical Framework Claims | The flaw description incorrectly claims the paper lacks specific references to equations, algorithms, or tables, when the paper explicitly includes Algorithm 1, Equation (1)-(3), and Table 1 to substa |
| `KOUAayk5Kx/flaw-2` | **not_paper_grounded** | Validation accuracy claims lack statistical grounding | The flaw is a generic critique about missing statistical tests, not a specific issue verifiable from the provided paper text. |

### Hygiene diagnostics (filtered-out flaws)

- filtered_out_total: **22** (raw-visible flaws that hygiene moved out of candidate/confirmed, plus flaws that were never visible)
- hygiene true positives (filtered & not_grounded by judge): **9**
- hygiene false negatives (filtered but actually paper_grounded): **13**
- **Hygiene_Precision** = 0.4091 (higher = hygiene was more correct in what it filtered)
- Hygiene_FN_Rate     = 0.5909 (real grounded flaws lost to over-aggressive hygiene)

## How to interpret

- **Grounded_Support_Precision** is the LLM-judged share of strong support evidence whose claim/evidence/stance triple is grounded in the paper text. It is the V2 红线 6 upgrade from `criterion_self_claimed_grounded_rate` (agent self-claimed) to a paper-text-aware judge.
- The three flaw views answer different paper questions:
    - `raw` answers: *how much of the flaw stream from the workers is grounded?*
    - `hygiene` answers: *how much of what the reviewer ultimately reads is grounded?*
    - `hygiene_evidence_aware` answers: *what would happen if we relaxed hygiene only for flaws that already cite real-strong evidence?*
- **Hygiene_Precision** quantifies how often the hygiene layer was right to filter a flaw. A high value (≥0.6) supports the conservative-by-design framing: the system prefers to lose some grounded flaws rather than expose hallucinated or schema-dump flaws to the reviewer.
- The bucket breakdown shows whether grounding rates differ across abstract / method / result citations — paper-side claims are usually grounded at higher rates than result-table-derived claims, so this slice matters for the paper narrative.
- `parse_error` rows are *not* counted as not_grounded; they are reported separately so prompt regressions are visible. If parse_error > 5% of total, refresh the prompt.

Generated by `scripts/judge_grounded_support_v1.py`.
