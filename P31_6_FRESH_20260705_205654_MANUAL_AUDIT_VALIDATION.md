# P31.6 Manual Audit Validation

- run: `P31_6_FRESH_20260705_205654`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 5 |
| `manual_A_clusters` | 2 |
| `manual_B_clusters` | 4 |
| `manual_A_B_clusters` | 6 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 5 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| B | HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | keep_with_careful_wording | The paper claims superior OrcaBench performance and discusses GPT-4 as a salient role-playing LLM, but the observed baseline section does not include a same-... |
| B | NnExMNiTHw | missing_ablation | acceptance_prediction_head | keep_with_careful_wording | The acceptance prediction head is central to the adaptive stopping policy. Existing comparisons show end-to-end gains over fixed-K speculative decoding, but ... |
| A | XH3OiIhtvf | negative_result | incorporating a secure aggregator in the federated model results in a less favor | keep_as_clear_issue | The audited quote directly contradicts or at least qualifies the claim that the secure aggregation step improves EER. This is a clear paper-grounded negative... |
| B | YXn76HMetm | missing_baseline | equalal_baseline | keep_with_careful_wording | HALO claims SOTA active learning under domain shift and names EqualAL as relevant prior work, but the audited evidence does not show EqualAL in the compariso... |
| B | a6SntIisgg | missing_ablation | global_encoder | keep_with_careful_wording | The Global Encoder is a named central branch in LogoRA. Existing ablations appear focused on losses rather than the global branch itself, so the concern is d... |
| A | fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | keep_as_clear_issue | The paper makes explicit efficiency claims, but the audited evidence does not provide concrete runtime, memory, FLOP, hardware, or communication-cost measure... |
