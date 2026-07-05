# P31.6 Entry Gate Audit

- dashboard: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527_HARDNEG20_DASHBOARD.json`
- review issue cases: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527_RECOVERY_CASE_TABLE.json`
- manual audit validation: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527_MANUAL_AUDIT_VALIDATION.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 5 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 5 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 5 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 11 | 11 | PASS |
| `dashboard_case_cluster_count_match` | 11 | 11 | PASS |
| `dashboard_recomputed_cluster_count_match` | 11 | 11 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 11 | <= 11 | PASS |
| `dashboard_origin_cluster_counts_sum` | 11 | 11 | PASS |
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
| `system_clusters` | 11 |
| `critique_origin_clusters` | 5 |
| `manual_A_clusters` | 2 |
| `manual_B_clusters` | 5 |
| `manual_A_B_clusters` | 7 |
| `manual_C_clusters` | 4 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `manual_A_B_clusters_by_origin` | {'critique_payload': 5, 'deterministic_seed': 1, 'quote_grounded': 1} |
| `manual_D_clusters_by_origin` | {} |
| `cluster_count_by_origin` | {'claim_obligation': 1, 'critique_payload': 5, 'deterministic_seed': 4, 'quote_grounded': 1} |
| `critique_origin_manual_A_B_clusters` | 5 |
| `deterministic_seed_manual_A_B_clusters` | 1 |
| `critique_origin_D_clusters` | 0 |
| `status` | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | claim-1, claim-3 | graph control module; component-isolation ablation for with a graph control module | Section 3.2 |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | claim-2 | same-setting comparison against paper-named GPT-4 baseline | Table/Figure excerpt #2 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2, claim-4 | acceptance prediction head; component-isolation ablation for of the acceptance prediction head | Section: SpecDec++: Theory and Algorithm |
| YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | claim-3 | same-setting comparison against paper-named PixelPick baseline; same-setting comparison against p... | Comparison / Robustness excerpt #1 |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | claim-1, claim-4 | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | paper inventory #1 |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | rim-c3-ma-graph-control-module-2 | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c2-ma-weighted-bce-loss | critique_direct_verified_cluster |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | rim-c2-mb-same-setting-comparison-against | critique_direct_verified_cluster |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | rim-c4-ec-runtime-memory-parameter-flop-ha | critique_direct_verified_cluster |

## Selected-Menu Failure Details

| paper | stage | reason | type | target | locator |
|---|---|---|---|---|---|
| ye3NrNrYOY | counterevidence | full_text_protocol_or_result_counterevidence | evaluation_protocol_risk | accuracy reporting protocol or comparability setting | Datasets. For the experiments that perform training and test |
| 7Dub7UXTXN | target_quality_guard | missing_ablation_target_low_confidence | missing_ablation | component-isolation ablation for ReLU | paper inventory #5 |
| WpXq5n8yLb | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | recurrent draft model | paper component inventory #1 |
| a6SntIisgg | counterevidence | full_text_evaluation_or_scope_counterevidence | scope_overclaim | held-out or coverage evaluation for source-to-target | paper inventory #1 |
| QAgwFiIY4p | counterevidence | full_text_baseline_or_comparison_counterevidence | missing_baseline | same-setting comparison against paper-named Graphormer baseline | paper inventory #11 |
| TPAj63ax4Y | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | zero-shot instance choice mechanism module | paper inventory #10 |
| mHv6wcBb0z | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | ablation isolating Noise Regularization module | paper inventory #1 |
| xUe1YqEgd6 | counterevidence | full_text_evaluation_or_scope_counterevidence | scope_overclaim | held-out or coverage evaluation for frame-by-frame | paper inventory #1 |
| KOUAayk5Kx | expectation_basis | reviewer_candidate_expectation_not_auditable_in_paper | efficiency_cost_gap | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for t... | Figure 4 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine and manual gates pass for this audit scope; paper-ready claims still require carrying the listed manual labels and wording caveats into the narrative.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if a later full-scope gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
