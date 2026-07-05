# P31.6 Manual Audit Validation

- run: `P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 4 |
| `manual_A_clusters` | 0 |
| `manual_B_clusters` | 4 |
| `manual_A_B_clusters` | 4 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 4 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| B | GE6iywJtsV | missing_ablation | consisting_constrain_module | Keep as a defensible paper-facing concern with normalized wording. | The target is a concrete central method component and no component ablation was found, but the extracted entity phrase is awkward and overlaps the broader Gr... |
| B | NnExMNiTHw | missing_ablation | acceptance_prediction_head | Keep as a defensible paper-facing concern with cautious attribution wording. | The component is concrete and central to the reported improvements, while the paper-text snippets do not show a corresponding ablation. |
| B | QAgwFiIY4p | missing_baseline | paper-named_graphormer_baseline | Keep as a defensible review concern with same-task caveat. | Graphormer is paper-named and relevant to the graph-transformer comparison space, but the verified claim is narrower than the full paper; the concern is usab... |
| B | YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | Keep as a defensible paper-facing concern with protocol caveat. | The omitted baselines are paper-named and close to the active-learning segmentation setting, but protocol comparability needs careful wording. |
