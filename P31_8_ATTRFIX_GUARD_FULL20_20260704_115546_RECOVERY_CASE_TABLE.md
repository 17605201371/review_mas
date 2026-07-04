# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 7 |
| bucket::committed_not_effective | 2 |
| bucket::effective_repair_without_verified_negative | 3 |
| bucket::verified_review_issue_repair | 6 |
| case_rows | 18 |
| effective_repair_not_verified_negative_repair | 9 |
| effective_repair_turns | 9 |
| evidence_bucket::obligation_grounded_review_issue | 6 |
| evidence_bucket::stale_reviewer_absence_audit | 4 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 9 |
| operation::record_diagnosis_pending_concern | 2 |
| operation::reject_patch | 5 |
| turns_with_verified_review_issue_bundle_evidence | 6 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| ye3NrNrYOY | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| 7Dub7UXTXN | 7 | attempted_not_committed |  |  | : | -> | {} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1, "stale_reviewer_absence_audit": 1} |
| 9zEBK3E9bX | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| 9zEBK3E9bX | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| WpXq5n8yLb | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| HPuLU6q7xq | 5 | attempted_not_committed |  |  | : | -> | {} |
| fGXyvmWpw6 | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-efficiency-cost-gap | -> | {} |
| QAgwFiIY4p | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| TPAj63ax4Y | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-baseline | -> | {} |
| mHv6wcBb0z | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-4 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 7 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->candidate | {"verified_review_negative": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for domain of causal representation. Target claim: 'The p... |
| ye3NrNrYOY | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for domain of causal representation. Target claim: 'The p... |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for sz-Softmax loss; observed inventory: Finally, we use class-balancing cross entropy loss and Lova´sz-Softmax loss to guide the pre-training. |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, or hardware measurement for SPOT. Target claim: '... |
| 9zEBK3E9bX | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for sz-Softmax loss; observed inventory: Finally, we use class-balancing cross entropy loss and Lova´sz-Softmax loss to guide the pre-training. |
| 9zEBK3E9bX | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-robustness-or-generaliza | stale_reviewer_absence_audit | missing_robustness_or_generalization |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing robustness or generalization concern; missing/mismatch item(s): held-out or coverage evaluation for state-of-the-art. Target claim... |
| WpXq5n8yLb | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| mHv6wcBb0z | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| YXn76HMetm | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-4-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for proposed HFR module; observed inventory: \input{figures/radius_quant_bound_active} \section{Hyperbolic Active Learning Optimization (HALO)} \label{sec:method} In this section, first we int... |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-comparison-2 | verified_review_negative | negative_result | review_negative_verified | Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system |
