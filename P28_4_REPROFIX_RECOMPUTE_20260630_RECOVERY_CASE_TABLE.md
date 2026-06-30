# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 6 |
| bucket::committed_not_effective | 6 |
| bucket::verified_review_issue_repair | 4 |
| case_rows | 16 |
| effective_repair_not_verified_negative_repair | 4 |
| effective_repair_turns | 4 |
| evidence_bucket::obligation_grounded_review_issue | 4 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 2 |
| evidence_bucket::support_only | 1 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 4 |
| operation::record_diagnosis_pending_concern | 3 |
| operation::reject_patch | 4 |
| operation::route_to_assessment_limitation | 3 |
| turns_with_verified_review_issue_bundle_evidence | 4 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| uOrfve3prk | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| uOrfve3prk | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-4 | partially_supported->unsupported | {"verified_review_negative": 1} |
| 9zEBK3E9bX | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-1 | open->recorded | {} |
| WpXq5n8yLb | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| NnExMNiTHw | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 4 | attempted_not_committed |  |  | : | -> | {} |
| fGXyvmWpw6 | 6 | attempted_not_committed |  |  | : | -> | {} |
| QAgwFiIY4p | 7 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| mHv6wcBb0z | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| YXn76HMetm | 3 | committed_not_effective | route_to_assessment_limitation | state_mutation_applied | flaw:flaw-1 | candidate->downgraded | {"support_only": 1} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-baseline | -> | {} |
| KOUAayk5Kx | 5 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-negative-quote-bank-quote-candidate-window-2 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uOrfve3prk | 7 | attempted_not_committed | evidence-2-turn-5 | verified_review_negative | evaluation_protocol_risk | review_negative_verified | Limitation / Gap / Negative evidence excerpt #2 | Note that $\alpha$ is a hyperparameter that must be tuned for each method, model, and sometimes even intervention feature and thus cannot be used to compare the effects of interventions across methods. |
| NnExMNiTHw | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for biases in the prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for implement a small prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for implement a small prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| QAgwFiIY4p | 7 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-1-1 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #1 | To overcome this, acceleration techniques such as sparse attention and linear attention could be explored, which will be our future work. |
| YXn76HMetm | 3 | committed_not_effective | evidence-ablation-1 | support_only | generic_gap |  | Table: results table | HALO improves over RIPU by +2.9\% mIoU with a 5\% budget, reaffirming the effectiveness of our approach on a novel dataset, as shown in Table \ref{tab:results_table}c. |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| KOUAayk5Kx | 5 | committed_not_effective | evidence-negative-quote-bank-quote-candidate-window-2-1 | quote-bank-negative-grounding_candidate | reproducibility_gap | insufficient_semantic_negative | Candidate negative window #2 | rsection region where both architectures $A$ and $B$ have low test error. • The proposed paradigm is integrated into two baselines, and a number of experimental results show that the OGL is able to mitigate the multi-... |
