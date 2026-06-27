# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 6 |
| bucket::committed_not_effective | 5 |
| bucket::effective_repair_without_verified_negative | 1 |
| bucket::verified_review_issue_repair | 2 |
| case_rows | 14 |
| effective_repair_not_verified_negative_repair | 3 |
| effective_repair_turns | 3 |
| evidence_bucket::obligation_grounded_review_issue | 2 |
| evidence_bucket::stale_reviewer_absence_audit | 1 |
| operation::mark_contested | 3 |
| operation::record_diagnosis_pending_concern | 5 |
| operation::reject_patch | 5 |
| turns_with_verified_review_issue_bundle_evidence | 2 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 7Dub7UXTXN | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XyB4VvF01X | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-insufficient-evaluation- | -> | {} |
| cklg91aPGk | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| fGXyvmWpw6 | 6 | attempted_not_committed | reject_patch | patch_validated | claim_requirement_gap:claim-2 | open->recorded | {} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | partially_supported->unsupported | {} |
| TPAj63ax4Y | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| mHv6wcBb0z | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| YXn76HMetm | 4 | attempted_not_committed |  |  | : | -> | {} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| KOUAayk5Kx | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table 1 | missing/mismatch: SECO baseline for label efficiency comparison; observed inventory: Table 1: Fine-tuning performance on NuScenes benchmark. P.D.A. represents the Pre-training Data Amount. We fine-tune on $5\%$ NuScenes training data. |
| XyB4VvF01X | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-empirical-result | stale_reviewer_absence_audit | result_claim_mismatch |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a result claim mismatch concern; missing/mismatch item(s): quantitative comparison table for k-NN baseline. Target claim: 'The proposed G2T-... |
| mHv6wcBb0z | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-method-detail | obligation_grounded_review_issue | method_support_gap | review_negative_absence_audit_verified | Section: Method | missing/mismatch: concrete specification of the noise type, distribution, and magnitude in NR-DCCA; observed inventory: \subsection{Method} Based on the discussions in previous sections, we present NR-DCCA, which makes use of the noise regularization approach to prev... |
