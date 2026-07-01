# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 17 |
| bucket::committed_not_effective | 2 |
| bucket::effective_repair_without_verified_negative | 2 |
| bucket::verified_review_issue_repair | 4 |
| case_rows | 25 |
| effective_repair_not_verified_negative_repair | 6 |
| effective_repair_turns | 6 |
| evidence_bucket::insufficient_claim_relation | 1 |
| evidence_bucket::missing_evidence_id | 1 |
| evidence_bucket::obligation_grounded_review_issue | 5 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 1 |
| evidence_bucket::stale_reviewer_absence_audit | 3 |
| evidence_bucket::support_only | 1 |
| operation::downgrade_claim_to_unsupported | 1 |
| operation::mark_contested | 6 |
| operation::reject_patch | 15 |
| operation::route_to_assessment_limitation | 1 |
| turns_with_verified_review_issue_bundle_evidence | 5 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| 7Dub7UXTXN | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-reproducibility-gap | -> | {} |
| 7Dub7UXTXN | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | supported->unsupported | {"missing_evidence_id": 1} |
| 9zEBK3E9bX | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-2-evaluation-protocol-risk | candidate->retracted | {} |
| 9zEBK3E9bX | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-2-evaluation-protocol-risk | candidate->retracted | {} |
| 9zEBK3E9bX | 6 | committed_not_effective | downgrade_claim_to_unsupported | patch_committed | claim:claim-1 | partially_supported->unsupported | {"obligation_grounded_review_issue": 1, "support_only": 1} |
| XyB4VvF01X | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {"insufficient_claim_relation": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-reproducibility-gap | -> | {} |
| WpXq5n8yLb | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | attempted_not_committed |  |  | : | -> | {} |
| NnExMNiTHw | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| cklg91aPGk | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| HPuLU6q7xq | 4 | attempted_not_committed |  |  | : | -> | {} |
| fGXyvmWpw6 | 4 | committed_not_effective | route_to_assessment_limitation | state_mutation_applied | flaw:flaw-1 | confirmed->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | candidate->retracted | {} |
| QAgwFiIY4p | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | candidate->retracted | {} |
| QAgwFiIY4p | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | -> | {} |
| TPAj63ax4Y | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| mHv6wcBb0z | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| mHv6wcBb0z | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| YXn76HMetm | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1, "stale_reviewer_absence_audit": 1} |
| YXn76HMetm | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-evaluation-protocol-risk | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7Dub7UXTXN | 7 | attempted_not_committed | evidence-1-turn-7 | missing_evidence_id |  |  |  |  |
| 9zEBK3E9bX | 6 | committed_not_effective | evidence-critique-negative-1 | support_only | negative_result | insufficient_semantic_negative | Limitation / Gap / Negative evidence excerpt #1 | 5 reveal that relying solely on detection as a pre-training task yields minimal performance gains, particularly |
| 9zEBK3E9bX | 6 | committed_not_effective | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for unified 3D scene representation; observed inventory: In this paper, SPOT is proposed to use 3D semantic occupancy prediction to learn a unified 3D scene representation for various downstream tasks inc... |
| XyB4VvF01X | 4 | attempted_not_committed | evidence-targeted-candidate-quote-neg-search-quote-claim-1-negative-result-quote | insufficient_claim_relation | negative_result | insufficient_claim_relation | Figure 6 | The addition of names in G2T-Named-Update fares slightly worse than the main G2T solver G2T-Anon-Update. |
| WpXq5n8yLb | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| cklg91aPGk | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-robustness-or-generaliza | stale_reviewer_absence_audit | missing_robustness_or_generalization |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing robustness or generalization concern; missing/mismatch item(s): held-out or coverage evaluation for GCL. Target claim: 'PROP achie... |
| fGXyvmWpw6 | 4 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-2-2 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | The first approach can be easily applied to distilled local datasets, while the second approach has limitations when adapting to federated virtual learning. |
| TPAj63ax4Y | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): standard RIS/segmentation baselines and datasets used by the claim scope. Target claim... |
| mHv6wcBb0z | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-evaluation-protocol-eval | stale_reviewer_absence_audit | evaluation_protocol_risk |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a evaluation protocol risk concern; missing/mismatch item(s): same-budget, same-hardware, or fair-comparison protocol for RIPU. Target claim... |
