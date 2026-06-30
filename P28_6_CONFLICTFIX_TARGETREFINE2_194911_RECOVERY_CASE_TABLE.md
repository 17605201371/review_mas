# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 12 |
| bucket::committed_not_effective | 3 |
| bucket::effective_repair_without_verified_negative | 8 |
| bucket::verified_review_issue_repair | 6 |
| case_rows | 29 |
| effective_repair_not_verified_negative_repair | 14 |
| effective_repair_turns | 14 |
| evidence_bucket::insufficient_claim_relation | 1 |
| evidence_bucket::not_verified_or_unknown | 1 |
| evidence_bucket::obligation_grounded_review_issue | 8 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 1 |
| evidence_bucket::stale_reviewer_absence_audit | 8 |
| operation::mark_contested | 14 |
| operation::record_diagnosis_pending_concern | 2 |
| operation::reject_patch | 9 |
| operation::route_to_assessment_limitation | 1 |
| turns_with_verified_review_issue_bundle_evidence | 7 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| 7Dub7UXTXN | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| 9zEBK3E9bX | 5 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"insufficient_claim_relation": 1} |
| GE6iywJtsV | 4 | attempted_not_committed |  |  | : | -> | {} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | uncertain->unsupported | {"obligation_grounded_review_issue": 2} |
| WpXq5n8yLb | 6 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-propgcl-by-excluding-trans | -> | {} |
| fGXyvmWpw6 | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| fGXyvmWpw6 | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| fGXyvmWpw6 | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| QAgwFiIY4p | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| QAgwFiIY4p | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| QAgwFiIY4p | 5 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| TPAj63ax4Y | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| mHv6wcBb0z | 3 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-missing-ablation | candidate->retracted | {} |
| mHv6wcBb0z | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-missing-ablation | candidate->retracted | {} |
| mHv6wcBb0z | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| mHv6wcBb0z | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | supported->unsupported | {"not_verified_or_unknown": 1} |
| YXn76HMetm | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| KOUAayk5Kx | 6 | attempted_not_committed |  |  | : | -> | {} |
| KOUAayk5Kx | 7 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-2-missing-ablation | candidate->retracted | {} |
| XH3OiIhtvf | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-4 | supported->supported | {"stale_reviewer_absence_audit": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for function generates the action representation. Target ... |
| 9zEBK3E9bX | 5 | committed_not_effective | evidence-critique-negative-1 | insufficient_claim_relation | negative_result | insufficient_claim_relation | Table 6 | 5 reveal that relying solely on detection as a pre-training task yields minimal performance gains, particularly |
| GE6iywJtsV | 5 | attempted_not_committed | evidence-reviewer-absence-claim-2-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for ControllNet; observed inventory: \section{2 METHODS } In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it comp... |
| GE6iywJtsV | 5 | attempted_not_committed | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for GrCN; observed inventory: \section{2 METHODS } In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it comp... |
| WpXq5n8yLb | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of the acceptance prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| a6SntIisgg | 5 | attempted_not_committed | evidence-negative-quote-bank-quote-negative-or-gap-2-2 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Section: Conclusion and Limitations | effectively, resulting in the successful alignment of diverse features. \section{Conclusion and Limitations} Through an investigation of previous works on UDA for time series, we find that existing methods do not suffici |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for fusion. Target claim: 'LogoRA uses a novel local-glob... |
| fGXyvmWpw6 | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for federated gradient. Target claim: 'The paper proposes... |
| fGXyvmWpw6 | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for federated gradient. Target claim: 'The method harmoni... |
| fGXyvmWpw6 | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for federated gradient. Target claim: 'The method harmoni... |
| QAgwFiIY4p | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for devise a Deepset-based set encoder. Target claim: 'Th... |
| TPAj63ax4Y | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for effective we expect the loss. Target claim: 'The fram... |
| mHv6wcBb0z | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Table 1 | missing/mismatch: Ablation on number of motion components (K) beyond K=4; observed inventory: Table 1: Ablation study for three main components of our method LT-MS $K=4,$ ) on DAVIS2016, FBMS59 and SegTrackV2. Only one model component is mod... |
| YXn76HMetm | 5 | attempted_not_committed | evidence-reviewer-absence-claim-3-baseline-or-comparison-m-turn-5 | not_verified_or_unknown | missing_baseline | insufficient_paper_grounding | Table 1 | HALO improves over the RIPU baseline by +2.9% mIoU with a 5% annotation budget on a novel dataset. |
| YXn76HMetm | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| YXn76HMetm | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| XH3OiIhtvf | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-4-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for training of deep neural network. Target claim: 'The m... |
