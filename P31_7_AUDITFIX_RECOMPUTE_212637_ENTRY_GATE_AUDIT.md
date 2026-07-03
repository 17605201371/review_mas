# P31.6 Entry Gate Audit

- dashboard: `P31_7_AUDITFIX_RECOMPUTE_212637_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_7_AUDITFIX_RECOMPUTE_212637_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_7_AUDITFIX_RECOMPUTE_212637_RECOVERY_CASE_TABLE.json`
- machine gate: **FAIL**
- manual gate: **REQUIRED**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_payload_verified_cluster_count` | 0 | >= 3 | FAIL |
| `candidate_menu_item_verified_count` | 0 | >= 2 | FAIL |
| `case_table_critique_origin_cluster_count` | 0 | >= 3 | FAIL |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 13 | 13 | PASS |
| `dashboard_case_cluster_count_match` | 13 | 13 | PASS |
| `dashboard_recomputed_cluster_count_match` | 13 | 13 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 13 | <= 13 | PASS |
| `dashboard_origin_cluster_counts_sum` | 13 | 13 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |

## Blocking Issues

- critique_payload_verified_cluster_count: actual 0, required >= 3
- candidate_menu_item_verified_count: actual 0, required >= 2
- case_table_critique_origin_cluster_count: actual 0, required >= 3

## Critique-Origin Clusters For Manual Audit

_No Critique-origin verified clusters found._

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
