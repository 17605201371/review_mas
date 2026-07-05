# P31.6 Manual Audit Validation

- run: `P31_28_POSTFIX_CRITIQUE5_20260705_185055`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 4 |
| `manual_A_clusters` | 1 |
| `manual_B_clusters` | 2 |
| `manual_A_B_clusters` | 3 |
| `manual_C_clusters` | 1 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 3 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| A | GE6iywJtsV | missing_ablation | graph_control_module | Keep as paper-facing Critique-origin issue. | Central method component is locatable in the paper and tied to the main constrained-generation claim; no paper-text counterevidence showed an ablation isolat... |
| B | NnExMNiTHw | missing_ablation | acceptance_prediction_head | Keep as defensible paper-facing concern with cautious wording. | The trained prediction head is a concrete method component and no ablation was found, but the cluster spans MDP/theory claims, so it is best framed as an att... |
| C | QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | Do not use as paper-facing Stage 2 success; keep only as diagnosis of over-sp... | The paper-grounded phrase is real, but the selected missing-ablation target is not a natural component-level obligation. This is weak diagnostic evidence, no... |
| B | YXn76HMetm | missing_baseline | equalal_baseline | Keep as defensible paper-facing concern with same-setting caveat. | EqualAL is paper-named and relevant to AL segmentation, while the empirical comparison section appears not to include it. The concern is defensible but proto... |
