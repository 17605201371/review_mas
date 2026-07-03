# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 22 |
| bucket::committed_not_effective | 3 |
| bucket::effective_repair_without_verified_negative | 2 |
| bucket::verified_review_issue_repair | 6 |
| case_rows | 33 |
| effective_repair_not_verified_negative_repair | 8 |
| effective_repair_turns | 8 |
| evidence_bucket::missing_evidence_id | 1 |
| evidence_bucket::obligation_grounded_review_issue | 9 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 2 |
| evidence_bucket::stale_reviewer_absence_audit | 1 |
| evidence_bucket::verified_review_negative | 2 |
| operation::downgrade_final_to_candidate | 1 |
| operation::mark_contested | 8 |
| operation::record_diagnosis_pending_concern | 2 |
| operation::reject_patch | 20 |
| turns_with_verified_review_issue_bundle_evidence | 9 |
| turns_with_verified_review_negative_evidence | 2 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| uOrfve3prk | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| 7Dub7UXTXN | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | uncertain->unsupported | {"obligation_grounded_review_issue": 1} |
| 9zEBK3E9bX | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"missing_evidence_id": 1} |
| XyB4VvF01X | 7 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| GE6iywJtsV | 3 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| GE6iywJtsV | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| WpXq5n8yLb | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| WpXq5n8yLb | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 5 | attempted_not_committed |  |  | : | -> | {} |
| NnExMNiTHw | 6 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | uncertain->unsupported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| a6SntIisgg | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 4 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-missing-robustness-or-ge | candidate->retracted | {} |
| cklg91aPGk | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-1-missing-robustness-or-ge | candidate->retracted | {} |
| cklg91aPGk | 7 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | unsupported->supported | {"obligation_grounded_review_issue": 1} |
| HPuLU6q7xq | 4 | attempted_not_committed |  |  | : | -> | {} |
| HPuLU6q7xq | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-ablation | -> | {} |
| fGXyvmWpw6 | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-efficiency-cost-gap | -> | {} |
| fGXyvmWpw6 | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-efficiency-cost-gap | -> | {} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-reproducibility-gap | -> | {} |
| QAgwFiIY4p | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| TPAj63ax4Y | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| TPAj63ax4Y | 7 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| mHv6wcBb0z | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| mHv6wcBb0z | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-baseline | -> | {} |
| XH3OiIhtvf | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | partially_supported->unsupported | {"verified_review_negative": 1} |
| XH3OiIhtvf | 7 | committed_not_effective | downgrade_final_to_candidate | patch_committed | flaw:flaw-1 | confirmed->candidate | {"verified_review_negative": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uOrfve3prk | 6 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-2-3 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | However, recent work points to key limitations of patching, particularly with respect to real-world utility in downstream applications such as model editing \citep{hase2024does, zhang2023towards}. |
| 7Dub7UXTXN | 4 | attempted_not_committed | evidence-reviewer-absence-claim-4-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: Overall, our results show that some properties established for bias-free ReLU networks arise due to equivalence to linear networks, and suggest tha... |
| 9zEBK3E9bX | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | missing_evidence_id |  |  |  |  |
| GE6iywJtsV | 3 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-1-1 | quote-bank-negative-grounding_candidate | negative_result | insufficient_claim_relation | Limitation / Gap / Negative evidence excerpt #1 | It is even worse for the best ones with a median of |
| GE6iywJtsV | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a graph control module; observed inventory: This approach allowed ControlNet to learn a diverse range of conditional models.(Zhang et al., 2023) Inspired by ControlNet, we introduce a novel d... |
| GE6iywJtsV | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a graph control module; observed inventory: This approach allowed ControlNet to learn a diverse range of conditional models.(Zhang et al., 2023) Inspired by ControlNet, we introduce a novel d... |
| WpXq5n8yLb | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 6 | attempted_not_committed | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for Global Encoder. Target claim: 'The paper proposes Log... |
| cklg91aPGk | 7 | attempted_not_committed | evidence-reviewer-absence-claim-1-robustness-or-generaliza | obligation_grounded_review_issue | missing_robustness_or_generalization | review_negative_absence_audit_verified | Table 8 | missing/mismatch: coverage or held-out evaluation for GCL; observed inventory: Thanks to exclusion of transformation weights, PROPGCL demonstrates superior efficiency compared to corresponding baseline methods in terms of both... |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper method inventory #1 | missing/mismatch: training hyperparameters, configuration, seed, or implementation detail for PST; observed inventory: To demonstrate the effectiveness of our approach, we introduce Point Set Transformer (PST), a transformer architecture that accepts a point set con... |
| mHv6wcBb0z | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for have designed a transformer-based network; observed inventory: More specifically, we have designed a transformer-based network, where we leverage a mathematically well-founded framework, the Evidence Lower Boun... |
| XH3OiIhtvf | 6 | attempted_not_committed | evidence-critique-negative-1 | verified_review_negative | result_claim_mismatch | review_negative_verified | Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 7 | committed_not_effective | evidence-critique-negative-1 | verified_review_negative | result_claim_mismatch | review_negative_verified | Figure 2 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
