# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 12 |
| bucket::committed_not_effective | 1 |
| bucket::verified_review_issue_repair | 3 |
| bucket::verified_review_negative_repair | 1 |
| case_rows | 17 |
| effective_repair_not_verified_negative_repair | 3 |
| effective_repair_turns | 4 |
| evidence_bucket::missing_evidence_id | 1 |
| evidence_bucket::obligation_grounded_review_issue | 3 |
| evidence_bucket::support_only | 1 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 4 |
| operation::record_diagnosis_pending_concern | 1 |
| operation::reject_patch | 10 |
| turns_with_verified_review_issue_bundle_evidence | 3 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | attempted_not_committed | reject_patch | patch_validated | claim:claim-2 | partially_supported->supported | {} |
| WNxlJJIEVj | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| 9zEBK3E9bX | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | candidate->retracted | {"missing_evidence_id": 1} |
| GE6iywJtsV | 4 | attempted_not_committed |  |  | : | -> | {} |
| GE6iywJtsV | 6 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-baseline | -> | {} |
| NnExMNiTHw | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| a6SntIisgg | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-logora-uses-a-novel-local- | -> | {} |
| cklg91aPGk | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {"support_only": 1} |
| fGXyvmWpw6 | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| fGXyvmWpw6 | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| QAgwFiIY4p | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| TPAj63ax4Y | 5 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| mHv6wcBb0z | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| KOUAayk5Kx | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-evaluation-protocol-risk | -> | {} |
| XH3OiIhtvf | 4 | verified_review_negative_repair | mark_contested | hygiene_delta_improved | flaw:flaw-1 | candidate->candidate | {"verified_review_negative": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: The performance of offline reinforcement learning (RL) is sensitive to the proportion of high-return trajectories in the offline dataset. |
| 9zEBK3E9bX | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-theory-or-proof-1-2 | missing_evidence_id |  |  |  |  |
| cklg91aPGk | 7 | attempted_not_committed | evidence-1-turn-5 | support_only | generic_gap |  | Table 7 | We further propose to only learn the propagation coefficients in the encoder of GCL, which achieves state-of-the-art performance on diverse no classification benchmarks. |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | Section: Experiments | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for PSRD; observed inventory: Moreover, our graph-to-set method is adaptable to various configurations. |
| mHv6wcBb0z | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| XH3OiIhtvf | 4 | verified_review_negative_repair | evidence-critique-negative-1 | verified_review_negative | negative_result | review_negative_verified | Table 1 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
