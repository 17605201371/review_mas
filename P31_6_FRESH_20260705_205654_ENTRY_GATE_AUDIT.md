# P31.6 Entry Gate Audit

- dashboard: `P31_6_FRESH_20260705_205654_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_6_FRESH_20260705_205654_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_6_FRESH_20260705_205654_RECOVERY_CASE_TABLE.json`
- machine gate: **PASS**
- manual gate: **REQUIRED**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 12 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 12 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 11 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 15 | 15 | PASS |
| `dashboard_case_cluster_count_match` | 15 | 15 | PASS |
| `dashboard_recomputed_cluster_count_match` | 15 | 15 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 15 | <= 15 | PASS |
| `dashboard_origin_cluster_counts_sum` | 15 | 15 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| 9zEBK3E9bX | missing_ablation | unified_scene_representation | claim-1 | unified 3D scene representation | paper component inventory #1 |
| GE6iywJtsV | missing_ablation | pockets_with_the_glide_module | claim-1 | pockets with the GLIDE module | paper component inventory #1 |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | claim-3 | same-setting comparison against paper-named GPT-4 baseline | Claim-matched evidence excerpt #1 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2, claim-5 | component-isolation ablation for of our trained prediction head | paper component inventory #1 |
| QAgwFiIY4p | missing_baseline | paper-named_graphormer_baseline | claim-2, claim-3 | same-setting comparison against paper-named Graphormer baseline | Section: Long Range Graph Benchmark |
| WpXq5n8yLb | missing_ablation | from_llms_improves_the_alignment | claim-1, claim-2 | from LLMs improves the alignment | paper component inventory #1 |
| YXn76HMetm | missing_baseline | equalal_baseline | claim-2, claim-5 | same-setting comparison against paper-named EqualAL baseline | Table: results table |
| a6SntIisgg | missing_ablation | global_encoder | claim-1 | Global Encoder | paper component inventory #1 |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | claim-1, claim-3 | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | Section: Method |
| mHv6wcBb0z | missing_ablation | generalized_noise_regularization | claim-2, claim-4 | component-isolation ablation for Noise Regularization | Section 3 |
| ye3NrNrYOY | missing_ablation | causal_representation | claim-2 | in causal representation | Conclusion / Discussion excerpt #1 |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| ye3NrNrYOY | missing_ablation | causal_representation | rim-c2-ma-in-causal-representation | critique_direct_verified_cluster |
| 9zEBK3E9bX | missing_ablation | unified_scene_representation | rim-c1-ma-unified-3d-scene-representation | critique_direct_verified_cluster |
| GE6iywJtsV | missing_ablation | pockets_with_the_glide_module | rim-c1-ma-pockets-with-the-glide-module | critique_direct_verified_cluster |
| WpXq5n8yLb | missing_ablation | from_llms_improves_the_alignment | rim-c1-ma-from-llms-improves-the-alignment | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c2-ma-weighted-bce-loss | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c5-ma-our-trained-prediction-head | critique_direct_verified_cluster |
| a6SntIisgg | missing_ablation | global_encoder | rim-c1-ma-global-encoder | critique_direct_verified_cluster |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | rim-c3-mb-same-setting-comparison-against | critique_direct_verified_cluster |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | rim-c3-ec-runtime-memory-parameter-flop-ha | critique_direct_verified_cluster |
| QAgwFiIY4p | missing_baseline | paper-named_graphormer_baseline | rim-c2-mb-same-setting-comparison-against | critique_direct_verified_cluster |
| mHv6wcBb0z | missing_ablation | generalized_noise_regularization | rim-c2-ma-proposed-noise-regularization-mo | critique_direct_verified_cluster |
| YXn76HMetm | missing_baseline | equalal_baseline | rim-c2-mb-same-setting-comparison-against | critique_direct_verified_cluster |

## Selected-Menu Failure Details

| paper | stage | reason | type | target | locator |
|---|---|---|---|---|---|
| WNxlJJIEVj | counterevidence | missing_entity_already_observed_in_inventory | scope_overclaim | held-out or coverage evaluation for low-return | Comparison / Robustness excerpt #1 |
| XH3OiIhtvf | bundle_verification | efficiency_cost_menu_already_observed_in_inventory | efficiency_cost_gap | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for t... | paper inventory #1 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
