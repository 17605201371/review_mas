# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 9 |
| bucket::committed_not_effective | 5 |
| bucket::verified_review_issue_repair | 1 |
| case_rows | 15 |
| effective_repair_not_verified_negative_repair | 1 |
| effective_repair_turns | 1 |
| evidence_bucket::missing_evidence_id | 1 |
| evidence_bucket::obligation_grounded_review_issue | 1 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 1 |
| evidence_bucket::support_only | 3 |
| operation::mark_contested | 1 |
| operation::record_diagnosis_pending_concern | 4 |
| operation::reject_patch | 8 |
| operation::route_to_assessment_limitation | 1 |
| turns_with_verified_review_issue_bundle_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->retracted | {} |
| uOrfve3prk | 7 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"support_only": 1} |
| 7Dub7UXTXN | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| GE6iywJtsV | 6 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| NnExMNiTHw | 5 | attempted_not_committed |  |  | : | -> | {} |
| NnExMNiTHw | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| fGXyvmWpw6 | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| QAgwFiIY4p | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| mHv6wcBb0z | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | supported->unsupported | {"missing_evidence_id": 1} |
| YXn76HMetm | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-2 | supported->supported | {"support_only": 2} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| KOUAayk5Kx | 6 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| XH3OiIhtvf | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | supported->unsupported | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uOrfve3prk | 7 | committed_not_effective | evidence-quote-negative-3 | support_only | scope_limitation | insufficient_semantic_negative | Table/Figure excerpt #1 | \caption{Evaluation of the Intervention Success Rate for each method. |
| NnExMNiTHw | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-empirical-result-insuffi | obligation_grounded_review_issue | insufficient_evaluation | review_negative_absence_audit_verified | Comparison / Robustness excerpt #1 | missing/mismatch: sensitivity analysis of the maximum candidate length hyperparameter; observed inventory: Compared with the baseline speculative decoding (SpecDec) with fixed candidate lengths, by adaptively determining the candidate lengths via a train... |
| fGXyvmWpw6 | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-3-1 | quote-bank-negative-grounding_candidate | negative_result | insufficient_claim_relation | Limitation / Gap / Negative evidence excerpt #3 | However, VHL is still worse than \ours{}, and the performance may result from the differences in synthesizing global virtual data. |
| mHv6wcBb0z | 6 | attempted_not_committed | evidence-critique-negative-1 | missing_evidence_id |  |  |  |  |
| YXn76HMetm | 4 | attempted_not_committed | evidence-1-turn-2 | support_only | generic_gap |  | Table: results table | HALO improves over RIPU by +2.9\% mIoU with a 5\% budget, reaffirming the effectiveness of our approach on a novel dataset, as shown in Table \ref{tab:results_table}c. |
| YXn76HMetm | 4 | attempted_not_committed | evidence-small-model-quote-bank-2-turn-2 | support_only | generic_gap |  | Table: results table | The ADA performances in Table \ref{tab:results_table} are also compared with the corresponding supervised domain adaptation baselines (Supervised DA). |
