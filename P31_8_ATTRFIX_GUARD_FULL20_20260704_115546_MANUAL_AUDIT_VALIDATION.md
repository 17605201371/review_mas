# P31.6 Manual Audit Validation

- run: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 6 |
| `manual_A_clusters` | 3 |
| `manual_B_clusters` | 3 |
| `manual_A_B_clusters` | 6 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 6 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| B | GE6iywJtsV | missing_ablation | graph_control_module | include_with_caution | Defensible concern: graph control module is central to Diff-Shape / GrCN, and the paper appears not to isolate it in ablation; however the inventory quote is... |
| A | NnExMNiTHw | missing_ablation | acceptance_prediction_head | include_paper_facing | Clear review-worthy issue: SpecDec++ attributes adaptive candidate length to a trained acceptance prediction head, but the paper text exposes no ablation iso... |
| A | WpXq5n8yLb | missing_ablation | recurrent_draft_model | include_paper_facing | Clear review-worthy issue: the recurrent draft model is a claimed performance driver, while the ablation section appears to omit an isolation of recurrence/R... |
| B | a6SntIisgg | missing_ablation | global_encoder | include_with_caution | Defensible concern: LogoRA claims a local/global/fusion architecture, and current ablations appear to cover losses/backbones rather than isolating the Global... |
| B | fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | include_with_caution | Defensible efficiency-review concern: the paper makes an efficiency claim, but appears to lack wall-clock/hardware/resource measurements. The original invent... |
| A | mHv6wcBb0z | missing_ablation | generalized_noise_regularization | include_paper_facing | Clear review-worthy issue: NR-DCCA centers on generalized noise regularization to prevent model collapse, but the paper text does not appear to isolate that ... |
