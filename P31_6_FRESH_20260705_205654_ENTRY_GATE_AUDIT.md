# P31.6 Entry Gate Audit

- dashboard: `P31_6_FRESH_20260705_205654_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_6_FRESH_20260705_205654_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_6_FRESH_20260705_205654_RECOVERY_CASE_TABLE.json`
- manual audit validation: `P31_6_FRESH_20260705_205654_MANUAL_AUDIT_VALIDATION.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 6 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 6 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 5 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 6 | 6 | PASS |
| `dashboard_case_cluster_count_match` | 6 | 6 | PASS |
| `dashboard_recomputed_cluster_count_match` | 6 | 6 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 6 | <= 6 | PASS |
| `dashboard_origin_cluster_counts_sum` | 6 | 6 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |
| `manual_audit_status` | PASS | PASS | PASS |
| `manual_critique_origin_A_B_clusters` | 5 | >= 3 | PASS |
| `manual_D_clusters` | 0 | 0 | PASS |
| `manual_unfilled_clusters` | 0 | 0 | PASS |

## Manual Audit Summary

| metric | value |
|---|---:|
| `system_clusters` | 6 |
| `critique_origin_clusters` | 5 |
| `manual_A_clusters` | 2 |
| `manual_B_clusters` | 4 |
| `manual_A_B_clusters` | 6 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `manual_A_B_clusters_by_origin` | {'critique_payload': 5, 'quote_grounded': 1} |
| `manual_D_clusters_by_origin` | {} |
| `cluster_count_by_origin` | {'critique_payload': 5, 'quote_grounded': 1} |
| `critique_origin_manual_A_B_clusters` | 5 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |
| `status` | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | claim-3 | same-setting comparison against paper-named GPT-4 baseline | Claim-matched evidence excerpt #1 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2, claim-5 | component-isolation ablation for of our trained prediction head | paper component inventory #1 |
| YXn76HMetm | missing_baseline | equalal_baseline | claim-2, claim-5 | same-setting comparison against paper-named EqualAL baseline | Table: results table |
| a6SntIisgg | missing_ablation | global_encoder | claim-1 | Global Encoder | paper component inventory #1 |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | claim-1, claim-3 | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | Section: Method |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c2-ma-weighted-bce-loss | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c5-ma-our-trained-prediction-head | critique_direct_verified_cluster |
| a6SntIisgg | missing_ablation | global_encoder | rim-c1-ma-global-encoder | critique_direct_verified_cluster |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | rim-c3-mb-same-setting-comparison-against | critique_direct_verified_cluster |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | rim-c3-ec-runtime-memory-parameter-flop-ha | critique_direct_verified_cluster |
| YXn76HMetm | missing_baseline | equalal_baseline | rim-c2-mb-same-setting-comparison-against | critique_direct_verified_cluster |

## Selected-Menu Failure Details

| paper | stage | reason | type | target | locator |
|---|---|---|---|---|---|
| ye3NrNrYOY | target_quality_guard | missing_ablation_target_malformed_fragment | missing_ablation | in causal representation | paper component inventory #1 |
| WNxlJJIEVj | counterevidence | missing_entity_already_observed_in_inventory | scope_overclaim | held-out or coverage evaluation for low-return | Comparison / Robustness excerpt #1 |
| 9zEBK3E9bX | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | unified 3D scene representation | paper component inventory #1 |
| GE6iywJtsV | target_quality_guard | missing_ablation_target_evaluation_tool | missing_ablation | pockets with the GLIDE module | paper component inventory #1 |
| WpXq5n8yLb | target_quality_guard | missing_ablation_target_malformed_fragment | missing_ablation | from LLMs improves the alignment | paper component inventory #1 |
| QAgwFiIY4p | counterevidence | full_text_baseline_or_comparison_counterevidence | missing_baseline | same-setting comparison against paper-named Graphormer baseline | paper inventory #11 |
| mHv6wcBb0z | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | ablation isolating proposed Noise Regularization module | paper inventory #1 |
| XH3OiIhtvf | bundle_verification | efficiency_cost_menu_already_observed_in_inventory | efficiency_cost_gap | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for t... | paper inventory #1 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine and manual gates pass for this audit scope; paper-ready claims still require carrying the listed manual labels and wording caveats into the narrative.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if a later full-scope gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
