# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 20 |
| bucket::committed_not_effective | 5 |
| bucket::effective_repair_without_verified_negative | 3 |
| bucket::verified_review_issue_repair | 8 |
| case_rows | 36 |
| effective_repair_not_verified_negative_repair | 11 |
| effective_repair_turns | 11 |
| evidence_bucket::missing_evidence_id | 4 |
| evidence_bucket::obligation_grounded_review_issue | 8 |
| evidence_bucket::stale_reviewer_absence_audit | 4 |
| evidence_bucket::support_only | 2 |
| evidence_bucket::verified_review_negative | 4 |
| operation::downgrade_final_to_candidate | 1 |
| operation::mark_contested | 11 |
| operation::record_diagnosis_pending_concern | 4 |
| operation::reject_patch | 17 |
| turns_with_verified_review_issue_bundle_evidence | 8 |
| turns_with_verified_review_negative_evidence | 4 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| WNxlJJIEVj | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| uOrfve3prk | 6 | attempted_not_committed | reject_patch | patch_validated | claim_requirement_gap:claim-2 | open->recorded | {} |
| uOrfve3prk | 7 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| 7Dub7UXTXN | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XyB4VvF01X | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-4-evaluation-protocol-risk | candidate->retracted | {"missing_evidence_id": 1} |
| XyB4VvF01X | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-4-evaluation-protocol-risk | candidate->retracted | {"missing_evidence_id": 1} |
| XyB4VvF01X | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | supported->unsupported | {"missing_evidence_id": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-2 | candidate->downgraded | {"missing_evidence_id": 1} |
| GE6iywJtsV | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 5 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | attempted_not_committed |  |  | : | -> | {} |
| a6SntIisgg | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | supported->unsupported | {"support_only": 2} |
| HPuLU6q7xq | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| fGXyvmWpw6 | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| fGXyvmWpw6 | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| fGXyvmWpw6 | 5 | attempted_not_committed | reject_patch | attempted | hypothesis:hypothesis-1 | -> | {} |
| QAgwFiIY4p | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| QAgwFiIY4p | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| QAgwFiIY4p | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1, "stale_reviewer_absence_audit": 1} |
| TPAj63ax4Y | 6 | attempted_not_committed |  |  | : | -> | {} |
| mHv6wcBb0z | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-ablation | -> | {} |
| mHv6wcBb0z | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-4-missing-ablation | candidate->retracted | {} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-4-missing-ablation | candidate->retracted | {} |
| YXn76HMetm | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-4-missing-ablation | candidate->retracted | {} |
| KOUAayk5Kx | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | -> | {} |
| XH3OiIhtvf | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | candidate->confirmed | {"verified_review_negative": 1} |
| XH3OiIhtvf | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | uncertain->unsupported | {"verified_review_negative": 1} |
| XH3OiIhtvf | 6 | attempted_not_committed | reject_patch | patch_validated | claim:claim-2 | uncertain->unsupported | {"verified_review_negative": 1} |
| XH3OiIhtvf | 7 | committed_not_effective | downgrade_final_to_candidate | patch_committed | flaw:flaw-2 | confirmed->candidate | {"verified_review_negative": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for Planning Module; observed inventory: Considering some diffusion-based RL methods generate subsequent trajectories for planning \citep{janner2022planning,ajay2023is}, in which abundant ... |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section 4.3 / Table 6 | missing/mismatch: Ablation comparing occupancy prediction against alternative pretext tasks (e.g., masked...; observed inventory: Table 6: Ablation study on pre-training strategies across different datasets. |
| XyB4VvF01X | 4 | attempted_not_committed | evidence-reviewer-absence-claim-4-evaluation-protocol-eval | missing_evidence_id |  |  |  |  |
| XyB4VvF01X | 5 | attempted_not_committed | evidence-reviewer-absence-claim-4-evaluation-protocol-eval | missing_evidence_id |  |  |  |  |
| XyB4VvF01X | 7 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-1-1 | missing_evidence_id |  |  |  |  |
| GE6iywJtsV | 5 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-1-2 | missing_evidence_id |  |  |  |  |
| GE6iywJtsV | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | Figure 2 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for GrCN; observed inventory: Figure 2: The detailed architecture of Diff-Shape, consisting of (a) 3D generation module and (b) constrain module. |
| WpXq5n8yLb | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of the acceptance prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of the acceptance prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| a6SntIisgg | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for from its proposed time-frequency encoder. Target clai... |
| cklg91aPGk | 7 | attempted_not_committed | evidence-2-turn-2 | support_only | generic_gap |  | Table 8 | Thanks to exclusion of transformation weights, PROPGCL demonstrates superior efficiency compared to corresponding baseline methods in terms of both computational time and memory usage. As shown in Table 8, PROP-GRACE |
| cklg91aPGk | 7 | attempted_not_committed | evidence-small-model-quote-bank-12-turn-4 | support_only | generic_gap |  | Table 2 | As shown in Table 2, the transformation weights learned by GCL are no better than random. The model with random weights $\mathbf{W}_{1}$ and $\mathbf{W}_{2}$ attains a performance of $71.42\%$ , remarkably close to the |
| fGXyvmWpw6 | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for aggregated gradients from cross-entropy loss. Target ... |
| QAgwFiIY4p | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for with greater encoder. Target claim: 'The paper propos... |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for with greater encoder. Target claim: 'The paper propos... |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for PSRD; observed inventory: In contrast, this paper introduces a novel graph-to-set conversion method that bijectively transforms interconnected nodes into a set of independen... |
| mHv6wcBb0z | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| XH3OiIhtvf | 3 | attempted_not_committed | evidence-critique-negative-2 | verified_review_negative | result_claim_mismatch | review_negative_verified | Table/Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 5 | attempted_not_committed | evidence-critique-negative-2 | verified_review_negative | result_claim_mismatch | review_negative_verified | Table/Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 6 | attempted_not_committed | evidence-critique-negative-2 | verified_review_negative | result_claim_mismatch | review_negative_verified | Table/Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 7 | committed_not_effective | evidence-critique-negative-2 | verified_review_negative | result_claim_mismatch | review_negative_verified | Table/Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
