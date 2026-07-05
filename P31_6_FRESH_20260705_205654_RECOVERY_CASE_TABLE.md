# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 12 |
| bucket::committed_not_effective | 3 |
| bucket::effective_repair_without_verified_negative | 11 |
| bucket::verified_review_issue_repair | 5 |
| case_rows | 31 |
| effective_repair_not_verified_negative_repair | 16 |
| effective_repair_turns | 16 |
| evidence_bucket::not_verified_or_unknown | 1 |
| evidence_bucket::obligation_grounded_review_issue | 5 |
| evidence_bucket::stale_reviewer_absence_audit | 12 |
| evidence_bucket::support_only | 1 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 16 |
| operation::record_diagnosis_pending_concern | 3 |
| operation::reject_patch | 11 |
| turns_with_verified_review_issue_bundle_evidence | 5 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| WNxlJJIEVj | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| uOrfve3prk | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| 7Dub7UXTXN | 5 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| GE6iywJtsV | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| GE6iywJtsV | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| WpXq5n8yLb | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| WpXq5n8yLb | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| NnExMNiTHw | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| NnExMNiTHw | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-5 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| cklg91aPGk | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| HPuLU6q7xq | 4 | attempted_not_committed |  |  | : | -> | {} |
| HPuLU6q7xq | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| fGXyvmWpw6 | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| fGXyvmWpw6 | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-baseline | -> | {} |
| QAgwFiIY4p | 6 | attempted_not_committed | reject_patch | attempted | claim_requirement_gap:claim-2 | open->recorded | {} |
| QAgwFiIY4p | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| TPAj63ax4Y | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| mHv6wcBb0z | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 2} |
| mHv6wcBb0z | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-4 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| mHv6wcBb0z | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| xUe1YqEgd6 | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-5 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->candidate | {"verified_review_negative": 1} |
| XH3OiIhtvf | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | candidate->confirmed | {"not_verified_or_unknown": 1, "support_only": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): in causal representation. Target claim: 'During adaptation, the model treats certain t... |
| 9zEBK3E9bX | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): unified 3D scene representation. Target claim: 'The paper proposes SPOT, a scalable pr... |
| GE6iywJtsV | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): pockets with the GLIDE module. Target claim: 'The paper introduces a Graph ControllNet... |
| GE6iywJtsV | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): pockets with the GLIDE module. Target claim: 'The paper introduces a Graph ControllNet... |
| WpXq5n8yLb | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): from LLMs improves the alignment. Target claim: 'ReDrafter leverages a recurrent neura... |
| WpXq5n8yLb | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for from LLMs improves the alignment. Target claim: 'ReDr... |
| NnExMNiTHw | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-5-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: SpecDec++: Theory and Algorithm | missing/mismatch: our trained prediction head; observed inventory: Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \... |
| fGXyvmWpw6 | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when t... |
| QAgwFiIY4p | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting comparison against paper-named Graphormer baseline. Target claim: 'PST (P... |
| TPAj63ax4Y | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting comparison against paper-named CLIP baseline. Target claim: 'The proposed... |
| mHv6wcBb0z | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): ablation isolating proposed Noise Regularization module. Target claim: 'The proposed N... |
| mHv6wcBb0z | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting comparison against paper-named MVTCAE baseline. Target claim: 'The propos... |
| mHv6wcBb0z | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-4-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for Noise Regularization. Target claim: 'The NR-DCCA meth... |
| mHv6wcBb0z | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting comparison against paper-named MVTCAE baseline. Target claim: 'Deep Canon... |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table: results table | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: For GTAV$\rightarrow$CS and CS$\rightarrow$ACDC, the mIoU is calculated on the shared 19 classes, whereas for SYNTHIA$\rightarrow$CS two mIoU value... |
| YXn76HMetm | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-5-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| XH3OiIhtvf | 6 | attempted_not_committed | evidence-critique-negative-1 | verified_review_negative | negative_result | review_negative_verified | Comparison Section / Table 1 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-1 | support_only | generic_gap | insufficient_paper_grounding | Fig. 2 | In contrast to the results shown in Fig. 2 (b), this highlights the crucial need to carefully evaluate the impact of a secure aggregator on EER results, indicating a possible trade-off between privacyenhancing measures |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-2 | not_verified_or_unknown | direct_contradiction | not_negative_evidence | Table 1 | Table 1 shows EER for 'Secure Aggregator' is 0.1586, which is higher (worse) than the 'Baseline' EER of 0.0612, contradicting the claim of improvement. |
