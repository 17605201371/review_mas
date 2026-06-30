# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 11 |
| bucket::committed_not_effective | 1 |
| bucket::verified_review_issue_repair | 5 |
| case_rows | 17 |
| effective_repair_not_verified_negative_repair | 5 |
| effective_repair_turns | 5 |
| evidence_bucket::obligation_grounded_review_issue | 6 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 1 |
| operation::downgrade_claim_to_unsupported | 1 |
| operation::mark_contested | 5 |
| operation::reject_patch | 7 |
| turns_with_verified_review_issue_bundle_evidence | 6 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| 9zEBK3E9bX | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| 9zEBK3E9bX | 5 | attempted_not_committed | reject_patch | attempted | claim_requirement_gap:claim-1 | open->recorded | {} |
| GE6iywJtsV | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 5 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 6 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {} |
| NnExMNiTHw | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-5 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 5 | attempted_not_committed |  |  | : | -> | {} |
| a6SntIisgg | 6 | attempted_not_committed |  |  | : | -> | {} |
| a6SntIisgg | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-the-proposed-method-uses-l | -> | {} |
| cklg91aPGk | 4 | committed_not_effective | downgrade_claim_to_unsupported | state_mutation_applied_no_hygiene_delta | claim:claim-1 | partially_supported->unsupported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| fGXyvmWpw6 | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| mHv6wcBb0z | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for class-balancing cross entropy loss; observed inventory: Secondly, as the existing datasets use LiDAR sensors with various numbers of laser beams and different category annotation strategies, we propose t... |
| GE6iywJtsV | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for ControllNet; observed inventory: \section{2 METHODS } In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it comp... |
| NnExMNiTHw | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-5-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| cklg91aPGk | 4 | committed_not_effective | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table 5 | missing/mismatch: recent GNN or graph-transformer baselines on the same graph benchmarks; observed inventory: Table 5: Test accuracy $(\%)$ of homophily node classification benchmarks, comparing PROPGCL with other baselines. Red indicates the best method, w... |
| fGXyvmWpw6 | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-2-2 | quote-bank-negative-grounding_candidate | scope_overclaim | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | The first approach can be easily applied to distilled local datasets, while the second approach has limitations when adapting to federated virtual learning. |
| fGXyvmWpw6 | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for aggregated gradients from cross-entropy loss; observed inventory: First, we utilize the distance loss $\mathcal{L}_{Dist}$~\cite{zhao2021dataset} for gradient matching: \begin{equation}\label{eq:GM_ours} \mathcal{... |
| mHv6wcBb0z | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
