# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 9 |
| bucket::committed_not_effective | 2 |
| bucket::verified_review_issue_repair | 8 |
| case_rows | 19 |
| effective_repair_not_verified_negative_repair | 8 |
| effective_repair_turns | 8 |
| evidence_bucket::obligation_grounded_review_issue | 8 |
| evidence_bucket::support_only | 2 |
| operation::mark_contested | 8 |
| operation::record_diagnosis_pending_concern | 2 |
| operation::reject_patch | 8 |
| turns_with_verified_review_issue_bundle_evidence | 8 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uOrfve3prk | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 7Dub7UXTXN | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| 9zEBK3E9bX | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| XyB4VvF01X | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-4 | supported->supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | -> | {} |
| GE6iywJtsV | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-scope-overclaim | -> | {} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| cklg91aPGk | 3 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | unsupported->supported | {"support_only": 2} |
| cklg91aPGk | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | -> | {} |
| QAgwFiIY4p | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| mHv6wcBb0z | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| mHv6wcBb0z | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 6 | attempted_not_committed |  |  | : | -> | {} |
| YXn76HMetm | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| KOUAayk5Kx | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XyB4VvF01X | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-4-evaluation-protocol-eval | obligation_grounded_review_issue | evaluation_protocol_risk | review_negative_absence_audit_verified | paper inventory #23 | missing/mismatch: explicit evaluation protocol details for protocol; observed inventory: The resulting list was then split such that the average percentage of theorems and of proof states in the training split is close to $90\%$ (in our... |
| GE6iywJtsV | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for GrCN; observed inventory: \section{2 METHODS } In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it comp... |
| WpXq5n8yLb | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-scope-coverage-scope-ove | obligation_grounded_review_issue | scope_overclaim | review_negative_absence_audit_verified | paper inventory #2 | missing/mismatch: held-out or coverage evaluation for fixed-K; observed inventory: However, previous methods often use simple heuristics to choose $K$, which may result in sub-optimal performance. |
| cklg91aPGk | 3 | attempted_not_committed | evidence-1-turn-2 | support_only | generic_gap |  | Table 5 | Table 5: Test accuracy $(\%)$ of homophily node classification benchmarks, comparing PROPGCL with other baselines. Red indicates the best method, while underlined represents the second-best. |
| cklg91aPGk | 3 | attempted_not_committed | evidence-small-model-quote-bank-4-turn-2 | support_only | generic_gap |  | Section: 6.2 EXPERIMENTAL RESULTS | GRACE) achieves the best results in 2 out of 5 benchmarks and attains an average performance of $70.22\%$ , second only to PolyGCL’s $71.68\%$ . Notably, PolyGCL is optimized for heterophily graphs, whereas PROP-DGI |
| cklg91aPGk | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-robustness-or-generaliza | obligation_grounded_review_issue | missing_robustness_or_generalization | review_negative_absence_audit_verified | Table 2 | missing/mismatch: held-out or coverage evaluation for GCL; observed inventory: As shown in Table 2, the transformation weights learned by GCL are no better than random. The model with random weights $\mathbf{W}_{1}$ and $\math... |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for PST; observed inventory: To demonstrate the effectiveness of our approach, we introduce Point Set Transformer (PST), a transformer architecture that accepts a point set con... |
| mHv6wcBb0z | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| YXn76HMetm | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #4 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
