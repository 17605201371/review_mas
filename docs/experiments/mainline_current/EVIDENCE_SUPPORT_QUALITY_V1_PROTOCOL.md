# Evidence Support Quality v1 Protocol

## Goal

This patch moves the project away from hard controller rules and toward evidence quality modeling.

The recent fulltest39 run showed that Evidence Binding Robustness v1 fixed fallback binding, but false accepts still happened because abstract-level positive statements were counted as accept-level `strong` support. The remaining issue is not target control; it is that `strong support` was too flat.

## Change

Evidence Support Quality v1 adds source-aware support calibration:

- Evidence items now carry `support_source_bucket`.
- Evidence items now carry `support_quality` and optional `support_quality_reason`.
- Positive support from abstract/title/conclusion-only sources is not allowed to remain accept-level `strong` support after state validation.
- Empirical/method/result/table/figure/ablation evidence can remain strong.

## Buckets

- `abstract`
- `method_or_approach`
- `result_or_experiment`
- `conclusion_or_discussion`
- `other_or_unspecified`

## Runtime Behavior

During evidence binding validation:

- fallback or unbound strong positive evidence is downgraded to medium;
- bound-real-claim abstract-only strong positive evidence is downgraded to medium;
- result/evaluation/experiment/table/figure/ablation strong support remains strong.

This is not a new controller and not a final-decision threshold hack. It changes what is allowed to count as accept-level evidence.

## Prompt Behavior

Evidence Agent is instructed that `strength="strong"` should be reserved for concrete method/result/experiment/table/figure/ablation evidence. Abstract-only positive statements should normally be medium.

## Why This Is Needed

Fulltest39 showed the patched hygiene rule accepted three rows, but all accepted rows were abstract-only:

| paper_id | gold | support_total | abstract | non_abstract |
|---|---|---:|---:|---:|
| `XyB4VvF01X` | reject | 3 | 3 | 0 |
| `gzqrANCF4g` | accept | 3 | 3 | 0 |
| `QAgwFiIY4p` | reject | 3 | 3 | 0 |

The true accept and the false accepts were indistinguishable under the old support-count feature. Therefore support source quality must be represented before final decision can be trusted.

## Offline Sanity on Existing Fulltest39 JSONL

Applying the quality adjustment offline to the existing JSONL collapses all current accept rows back to reject:

| View | Pred Accept | True Accept | False Accept | Macro-F1 |
|---|---:|---:|---:|---:|
| patched hygiene rule | 3 | 1 | 2 | 0.5076 |
| quality-adjusted view | 0 | 0 | 0 | 0.4348 |

This is expected: the current 4B output did not produce result-level accept evidence for those rows. The next run must test whether the improved Evidence Agent prompt and state validator push the agent toward method/result/table/ablation evidence rather than abstract-only support.

## Keep / Revert Rule

Keep this patch if a rerun shows:

- fallback/unbound strong support remains zero;
- abstract-only strong support decreases;
- result/evaluation/table/ablation strong support appears on true accept rows;
- false accepts do not increase.

Revert or revise if:

- Evidence Agent cannot produce non-abstract support even when the paper contains it;
- all accept recovery disappears without improving evidence diagnostics;
- JSON fallback increases sharply.
