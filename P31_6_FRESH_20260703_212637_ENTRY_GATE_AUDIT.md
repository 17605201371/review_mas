# P31.6 Entry Gate Audit

- dashboard: `P31_6_FRESH_20260703_212637_HARDNEG20_DASHBOARD.json`
- review issue cases: `P31_6_FRESH_20260703_212637_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P31_6_FRESH_20260703_212637_RECOVERY_CASE_TABLE.json`
- machine gate: **FAIL**
- manual gate: **REQUIRED**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_payload_verified_cluster_count` | 1 | >= 3 | FAIL |
| `case_table_critique_origin_cluster_count` | 1 | >= 3 | FAIL |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |

## Blocking Issues

- critique_payload_verified_cluster_count: actual 1, required >= 3
- case_table_critique_origin_cluster_count: actual 1, required >= 3

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| 7Dub7UXTXN | missing_robustness_or_generalization | robustness_learning_rate | claim-2 | robustness to learning rate; robustness to network width; robustness to dataset variation | paper inventory #8 |

## Red-Flag Scan

_No simple lexical red flags found in verified issue cases._

## Notes

- Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
