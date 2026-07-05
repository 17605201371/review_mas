# P31.6 Entry Gate Audit

- dashboard: `P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123_RECOVERY_CASE_TABLE.json`
- manual audit validation: `P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_193123.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 4 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 4 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 4 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 5 | 5 | PASS |
| `dashboard_case_cluster_count_match` | 5 | 5 | PASS |
| `dashboard_recomputed_cluster_count_match` | 5 | 5 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 5 | <= 5 | PASS |
| `dashboard_origin_cluster_counts_sum` | 5 | 5 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |
| `manual_audit_status` | PASS | PASS | PASS |
| `manual_critique_origin_A_B_clusters` | 4 | >= 3 | PASS |
| `manual_D_clusters` | 0 | 0 | PASS |
| `manual_unfilled_clusters` | 0 | 0 | PASS |

## Manual Audit Summary

| metric | value |
|---|---:|
| `system_clusters` | 4 |
| `critique_origin_clusters` | 4 |
| `manual_A_clusters` | 0 |
| `manual_B_clusters` | 4 |
| `manual_A_B_clusters` | 4 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `manual_A_B_clusters_by_origin` | {'critique_payload': 4} |
| `manual_D_clusters_by_origin` | {} |
| `cluster_count_by_origin` | {'critique_payload': 4} |
| `critique_origin_manual_A_B_clusters` | 4 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |
| `status` | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | consisting_constrain_module | claim-2 | consisting of a constrain module | paper component inventory #1 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2 | acceptance prediction head; component-isolation ablation for trained acceptance prediction head | Comparison / Robustness excerpt #1 |
| QAgwFiIY4p | missing_baseline | paper-named_graphormer_baseline | claim-3 | same-setting comparison against paper-named Graphormer baseline | paper inventory #11 |
| YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | claim-3 | same-setting comparison against paper-named PixelPick baseline; same-setting comparison against p... | Table: main ablation |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | consisting_constrain_module | rim-c2-ma-consisting-of-a-constrain-module | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c2-ma-acceptance-prediction-head-3 | critique_direct_verified_cluster |
| QAgwFiIY4p | missing_baseline | paper-named_graphormer_baseline | rim-c3-mb-same-setting-comparison-against | critique_direct_verified_cluster |

## Selected-Menu Failure Details

| paper | stage | reason | type | target | locator |
|---|---|---|---|---|---|
| 9zEBK3E9bX | bundle_verification_or_not_materialized | not_verified_by_bundle | efficiency_cost_gap | wall-clock latency or throughput | Theory / Proof excerpt #1 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine and manual gates pass for this audit scope; paper-ready claims still require carrying the listed manual labels and wording caveats into the narrative.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if a later full-scope gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
