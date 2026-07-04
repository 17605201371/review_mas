# P31.6 Entry Gate Audit

- dashboard: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_RECOVERY_CASE_TABLE.json`
- manual audit validation: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_MANUAL_AUDIT_VALIDATION.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_payload_verified_cluster_count` | 6 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 7 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 6 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 14 | 14 | PASS |
| `dashboard_case_cluster_count_match` | 14 | 14 | PASS |
| `dashboard_recomputed_cluster_count_match` | 14 | 14 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 14 | <= 14 | PASS |
| `dashboard_origin_cluster_counts_sum` | 14 | 14 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |
| `manual_audit_status` | PASS | PASS | PASS |
| `manual_critique_origin_A_B_clusters` | 6 | >= 3 | PASS |
| `manual_D_clusters` | 0 | 0 | PASS |
| `manual_unfilled_clusters` | 0 | 0 | PASS |

## Manual Audit Summary

| metric | value |
|---|---:|
| `system_clusters` | 6 |
| `critique_origin_clusters` | 6 |
| `manual_A_clusters` | 3 |
| `manual_B_clusters` | 3 |
| `manual_A_B_clusters` | 6 |
| `manual_C_clusters` | 0 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `manual_A_B_clusters_by_origin` | {'critique_payload': 6} |
| `manual_D_clusters_by_origin` | {} |
| `cluster_count_by_origin` | {'critique_payload': 6} |
| `critique_origin_manual_A_B_clusters` | 6 |
| `deterministic_seed_manual_A_B_clusters` | 0 |
| `critique_origin_D_clusters` | 0 |
| `status` | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | claim-1, claim-2, claim-4 | component-isolation ablation for graph control module | paper component inventory #1 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2 | component-isolation ablation for train an acceptance prediction head | paper component inventory #1 |
| WpXq5n8yLb | missing_ablation | recurrent_draft_model | claim-1 | component-isolation ablation for recurrent neural network | paper component inventory #1 |
| a6SntIisgg | missing_ablation | global_encoder | claim-1 | component-isolation ablation for Global Encoder | paper component inventory #1 |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | claim-1, claim-2, claim-3 | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | paper inventory #1 |
| mHv6wcBb0z | missing_ablation | generalized_noise_regularization | claim-2 | component-isolation ablation for with a generalized noise regularization | paper component inventory #1 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
