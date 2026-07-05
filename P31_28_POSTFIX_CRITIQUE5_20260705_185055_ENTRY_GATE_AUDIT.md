# P31.6 Entry Gate Audit

- dashboard: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_RECOVERY_CASE_TABLE.json`
- manual audit validation: `P31_28_POSTFIX_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_185055.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 4 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 4 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 4 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 11 | 11 | PASS |
| `dashboard_case_cluster_count_match` | 11 | 11 | PASS |
| `dashboard_recomputed_cluster_count_match` | 11 | 11 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 11 | <= 11 | PASS |
| `dashboard_origin_cluster_counts_sum` | 11 | 11 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |
| `lexical_red_flag_count` | 0 | 0 | PASS |
| `manual_audit_status` | PASS | PASS | PASS |
| `manual_critique_origin_A_B_clusters` | 3 | >= 3 | PASS |
| `manual_D_clusters` | 0 | 0 | PASS |
| `manual_unfilled_clusters` | 0 | 0 | PASS |

## Manual Audit Summary

| metric | value |
|---|---:|
| `system_clusters` | 4 |
| `critique_origin_clusters` | 4 |
| `manual_A_clusters` | 1 |
| `manual_B_clusters` | 2 |
| `manual_A_B_clusters` | 3 |
| `manual_C_clusters` | 1 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `manual_A_B_clusters_by_origin` | {'critique_payload': 3} |
| `manual_D_clusters_by_origin` | {} |
| `cluster_count_by_origin` | {'critique_payload': 4} |
| `critique_origin_manual_A_B_clusters` | 3 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |
| `status` | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | claim-1 | graph control module | paper component inventory #1 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2 | our trained prediction head; component-isolation ablation for of the acceptance prediction head | paper component inventory #1 |
| QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | claim-1 | y coordinates without information loss | paper component inventory #1 |
| YXn76HMetm | missing_baseline | equalal_baseline | claim-3 | same-setting comparison against paper-named EqualAL baseline | Table: results table |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | rim-c1-ma-graph-control-module-2 | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c2-ma-our-trained-prediction-head | critique_direct_verified_cluster |
| QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | rim-c1-ma-y-coordinates-without-informatio | critique_direct_verified_cluster |
| YXn76HMetm | missing_baseline | equalal_baseline | rim-c3-mb-same-setting-comparison-against | critique_direct_verified_cluster |

## Selected-Menu Failure Details

_No selected-menu failure details found._

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine and manual gates pass for this audit scope; paper-ready claims still require carrying the listed manual labels and wording caveats into the narrative.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if a later full-scope gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
