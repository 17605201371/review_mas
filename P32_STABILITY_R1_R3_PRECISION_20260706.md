# P32 Stability Report

- status: **PASS**
- runs included: `2` / `2`
- runs excluded: `0`

## Acceptance Checks

| check | actual | required | status |
|---|---:|---:|---|
| `minimum_clean_runs` | 2 | 2 | PASS |
| `all_clean_runs_complete` | True | True | PASS |
| `all_protection_pass` | True | True | PASS |
| `harmful_recovery_total` | 0 | 0 | PASS |
| `max_manual_D_rate` | 0.000 | <= 0.0 | PASS |
| `recurring_A_B_clusters` | 6 | >= 1 | PASS |
| `recurring_critique_origin_A_B_clusters` | 5 | >= 1 | PASS |

## Run Summary

| label | rows | included | machine | manual | A/B | D | D rate | Critique A/B | harmful recovery | blockers |
|---|---:|---|---|---|---:|---:|---:|---:|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | 20 | yes | PASS | PASS | 7 | 0 | 0.000 | 5 | 0 |  |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | 20 | yes | PASS | PASS | 7 | 0 | 0.000 | 5 | 0 |  |

## Stability Metrics

| metric | count | mean | stdev | min | max |
|---|---:|---:|---:|---:|---:|
| `manual_A_B_cluster_count_stats` | 2 | 7 | 0.000 | 7 | 7 |
| `manual_D_rate_stats` | 2 | 0.000 | 0.000 | 0.000 | 0.000 |
| `accepted_cluster_jaccard_stats` | 1 | 0.750 | 0.000 | 0.750 | 0.750 |
| `critique_origin_cluster_jaccard_stats` | 1 | 1.000 | 0.000 | 1.000 | 1.000 |

## Recurrence

### Accepted Clusters

| item | runs |
|---|---:|
| `fgxyvmwpw6|efficiency_cost_gap|efficiency_resource_measurement` | 2 |
| `ge6iywjtsv|missing_ablation|graph_control_module` | 2 |
| `hpulu6q7xq|missing_baseline|paper-named_gpt-4_baseline` | 2 |
| `nnexmnithw|missing_ablation|acceptance_prediction_head` | 2 |
| `wpxq5n8ylb|missing_ablation|recurrent_draft_model` | 2 |
| `yxn76hmetm|missing_baseline|paper-named_pixelpick_baseline` | 2 |
| `hpulu6q7xq|missing_ablation|modeling_coarse_and_fine-grained_fusion` | 1 |
| `xh3oiihtvf|negative_result|incorporating a secure aggregator in the federated model results in a less favor` | 1 |

### Critique-Origin Accepted Clusters

| item | runs |
|---|---:|
| `fgxyvmwpw6|efficiency_cost_gap|efficiency_resource_measurement` | 2 |
| `ge6iywjtsv|missing_ablation|graph_control_module` | 2 |
| `hpulu6q7xq|missing_baseline|paper-named_gpt-4_baseline` | 2 |
| `nnexmnithw|missing_ablation|acceptance_prediction_head` | 2 |
| `yxn76hmetm|missing_baseline|paper-named_pixelpick_baseline` | 2 |

### Same-Paper Issue Recurrence

| item | runs |
|---|---:|
| `fgxyvmwpw6` | 2 |
| `ge6iywjtsv` | 2 |
| `hpulu6q7xq` | 2 |
| `nnexmnithw` | 2 |
| `wpxq5n8ylb` | 2 |
| `yxn76hmetm` | 2 |
| `xh3oiihtvf` | 1 |

### Same-Target Entity Recurrence

| item | runs |
|---|---:|
| `acceptance_prediction_head` | 2 |
| `efficiency_resource_measurement` | 2 |
| `graph_control_module` | 2 |
| `paper-named_gpt-4_baseline` | 2 |
| `paper-named_pixelpick_baseline` | 2 |
| `recurrent_draft_model` | 2 |
| `incorporating a secure aggregator in the federated model results in a less favor` | 1 |
| `modeling_coarse_and_fine-grained_fusion` | 1 |

## Notes

- Partial runs are excluded from clean-run acceptance even when they contain useful diagnostic rows.
- This report summarizes existing artifacts only; it does not relax verifier, manual-audit, or recovery gates.
