# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::assessment_limitation_routing | 1 |
| bucket::attempted_not_committed | 2 |
| bucket::committed_not_effective | 5 |
| bucket::effective_repair_without_verified_negative | 4 |
| bucket::verified_review_issue_repair | 5 |
| bucket::verified_review_negative_repair | 1 |
| case_rows | 18 |
| effective_repair_not_verified_negative_repair | 10 |
| effective_repair_turns | 11 |
| evidence_bucket::obligation_grounded_review_issue | 6 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 3 |
| evidence_bucket::stale_reviewer_absence_audit | 5 |
| evidence_bucket::verified_review_negative | 1 |
| operation::downgrade_claim_to_unsupported | 1 |
| operation::mark_contested | 10 |
| operation::record_diagnosis_pending_concern | 2 |
| operation::reject_patch | 1 |
| operation::route_to_assessment_limitation | 3 |
| turns_with_verified_review_issue_bundle_evidence | 6 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 7Dub7UXTXN | 4 | attempted_not_committed |  |  | : | -> | {} |
| 7Dub7UXTXN | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1, "stale_reviewer_absence_audit": 1} |
| 9zEBK3E9bX | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| 9zEBK3E9bX | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XyB4VvF01X | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 6 | committed_not_effective | downgrade_claim_to_unsupported | patch_committed | claim:claim-1 | uncertain->unsupported | {"obligation_grounded_review_issue": 1} |
| HPuLU6q7xq | 4 | assessment_limitation_routing | route_to_assessment_limitation | hygiene_delta_improved | flaw:flaw-reviewer-absence-claim-3-scope-overclaim | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| fGXyvmWpw6 | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| fGXyvmWpw6 | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| QAgwFiIY4p | 7 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| TPAj63ax4Y | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-insufficient-evaluation | -> | {} |
| mHv6wcBb0z | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| KOUAayk5Kx | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-reviewer-absence-claim-1-missing-ablation | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| XH3OiIhtvf | 6 | verified_review_negative_repair | mark_contested | hygiene_delta_improved | flaw:flaw-1 | candidate->candidate | {"verified_review_negative": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7Dub7UXTXN | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting baseline or comparison for the claimed improvement. Target claim: 'Empiri... |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Fig. 2 | missing/mismatch: component-isolation ablation for the claimed mechanism; observed inventory: We discuss the proposed SPOT in detail. As shown in Fig. 2, SPOT contains four parts: (a) Augmentations on LiDAR point clouds. (b) Encoder for LiDA... |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-efficiency-cost | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, hardware, or compute-cost comparison. Target clai... |
| 9zEBK3E9bX | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Table 6 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost comparison; observed inventory: Table 6: Ablation study on pre-training strategies across different datasets. |
| 9zEBK3E9bX | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Table 6 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost comparison; observed inventory: Table 6: Ablation study on pre-training strategies across different datasets. |
| XyB4VvF01X | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-efficiency-cost | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, hardware, or compute-cost comparison. Target clai... |
| cklg91aPGk | 6 | committed_not_effective | evidence-reviewer-absence-claim-1-method-detail | obligation_grounded_review_issue | method_support_gap | review_negative_absence_audit_verified | paper inventory #2 | missing/mismatch: clear definition of PROP; empirical results for PROP (not PROPGCL); observed inventory: In light of these insights, we enhance PROP with learnable propagation, introducing a novel GCL method termed PROPGCL. |
| HPuLU6q7xq | 4 | assessment_limitation_routing | evidence-negative-quote-bank-quote-critique-negative-2-1 | quote-bank-negative-grounding_candidate | scope_overclaim | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | \item \textbf{Limitations of the implicit modeling.} How to fuse personality trait score vectors is a challenge, this paper only presents a feasible idea, more appropriate methods are yet to be proposed. |
| fGXyvmWpw6 | 4 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-4-2 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #4 | The potential limitation lies in the additional communication and computation cost in data distillation, but we show that the trade-off is acceptable and can be mitigated by decreasing distillation \textit{iterations}... |
| fGXyvmWpw6 | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-efficiency-cost | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, hardware, or compute-cost comparison. Target clai... |
| mHv6wcBb0z | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-empirical-result | obligation_grounded_review_issue | insufficient_evaluation | review_negative_absence_audit_verified | paper inventory #6 | missing/mismatch: quantitative result table or metric for the claimed empirical effect; observed inventory: The developed NR-DCCA outperforms baselines stably and consistently in both synthetic and real-world datasets, and the proposed noise regularizatio... |
| xUe1YqEgd6 | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-reproducibility-detail | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | Table 1 | missing/mismatch: Explicit specification of the clustering algorithm used for segmentation; observed inventory: Table 1: Ablation study for three main components of our method LT-MS $K=4,$ ) on DAVIS2016, FBMS59 and SegTrackV2. Only one model component is mod... |
| YXn76HMetm | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-ablation-or-component | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for the claimed mechanism. Target claim: 'The hyperbolic ... |
| KOUAayk5Kx | 4 | committed_not_effective | evidence-negative-quote-bank-quote-results-1-4 | quote-bank-negative-grounding_candidate | scope_limitation | insufficient_claim_relation | Section: 2.1 ONE-SHOT NAS AND ISSUE OF MULTI-MODEL FORGETTING | In the training of one-shot NAS, each candidate architecture $\alpha$ inherits weights from the supernet $\mathcal{W}_{A}$ and directly evaluates it on the validation dataset without training. |
| XH3OiIhtvf | 6 | verified_review_negative_repair | evidence-critique-negative-1 | verified_review_negative | negative_result | review_negative_verified | Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
