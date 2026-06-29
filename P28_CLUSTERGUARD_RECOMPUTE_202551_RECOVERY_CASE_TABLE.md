# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 17 |
| bucket::committed_not_effective | 4 |
| bucket::effective_repair_without_verified_negative | 3 |
| bucket::verified_review_issue_repair | 5 |
| case_rows | 29 |
| effective_repair_not_verified_negative_repair | 8 |
| effective_repair_turns | 8 |
| evidence_bucket::not_verified_or_unknown | 2 |
| evidence_bucket::obligation_grounded_review_issue | 5 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 1 |
| evidence_bucket::stale_reviewer_absence_audit | 3 |
| evidence_bucket::support_only | 8 |
| operation::mark_contested | 8 |
| operation::record_diagnosis_pending_concern | 4 |
| operation::reject_patch | 11 |
| turns_with_verified_review_issue_bundle_evidence | 5 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| WNxlJJIEVj | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| uOrfve3prk | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| 7Dub7UXTXN | 5 | attempted_not_committed |  |  | : | -> | {} |
| 7Dub7UXTXN | 6 | attempted_not_committed | reject_patch | patch_validated | claim:claim-2 | partially_supported->unsupported | {"not_verified_or_unknown": 1} |
| 7Dub7UXTXN | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | unsupported->supported | {"support_only": 2} |
| 9zEBK3E9bX | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-1 | open->recorded | {} |
| XyB4VvF01X | 4 | attempted_not_committed | reject_patch | attempted | claim_requirement_gap:claim-1 | open->recorded | {} |
| XyB4VvF01X | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| GE6iywJtsV | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| WpXq5n8yLb | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-3 | uncertain->partially_supported | {"support_only": 1} |
| WpXq5n8yLb | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-3 | uncertain->partially_supported | {"support_only": 1} |
| WpXq5n8yLb | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| NnExMNiTHw | 5 | attempted_not_committed |  |  | : | -> | {} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | partially_supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| cklg91aPGk | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| fGXyvmWpw6 | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-4 | uncertain->unsupported | {"not_verified_or_unknown": 1} |
| fGXyvmWpw6 | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| mHv6wcBb0z | 4 | attempted_not_committed |  |  | : | -> | {} |
| mHv6wcBb0z | 5 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | unsupported->supported | {"support_only": 2} |
| mHv6wcBb0z | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | unsupported->supported | {"support_only": 2} |
| YXn76HMetm | 5 | attempted_not_committed |  |  | : | -> | {} |
| YXn76HMetm | 6 | attempted_not_committed |  |  | : | -> | {} |
| KOUAayk5Kx | 4 | attempted_not_committed |  |  | : | -> | {} |
| KOUAayk5Kx | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| KOUAayk5Kx | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting baseline comparison for state-reward. Target claim: 'An ablation study va... |
| uOrfve3prk | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-reproducibility-detail-r | obligation_grounded_review_issue | reproducibility_gap | review_negative_absence_audit_verified | paper inventory #47 | missing/mismatch: training hyperparameters, split, seed, code/config, or implementation detail for trade-off; specific implementation details or code for in-place editing; observed inventory: Note that $\alpha$ is a hyperparameter that must be tuned for each method, model, and sometimes even intervention feature and thus cannot be used t... |
| 7Dub7UXTXN | 6 | attempted_not_committed | evidence-critique-negative-1 | not_verified_or_unknown | missing_ablation | insufficient_paper_grounding | results section | bias-free ReLU networks have the same learning dynamics as linear networks when trained on symmetric datasets with square loss or logistic loss |
| 7Dub7UXTXN | 7 | attempted_not_committed | evidence-1 | support_only | generic_gap | insufficient_paper_grounding | Section 3.1 | For expressivity, we show that two-layer bias-free (leaky) ReLU networks cannot express odd functions except linear functions. |
| 7Dub7UXTXN | 7 | attempted_not_committed | evidence-small-model-quote-bank-4-turn-5 | support_only | generic_gap |  | Table/Figure excerpt #1 | \caption{Two-layer bias-free (leaky) ReLU networks that evolve like a linear network. |
| WpXq5n8yLb | 4 | attempted_not_committed | quote-critique-negative-1 | support_only | negative_result | insufficient_semantic_negative | Figure: tree attention ablation | We fix beam length to 5, beam width to 45, and tune batch size to push the compute limit, Figure~\ref{fig:tree-attention-ablation} (right) shows that when the batch size is below 4, computational resources are abundan... |
| WpXq5n8yLb | 5 | attempted_not_committed | quote-critique-negative-1 | support_only | negative_result | insufficient_semantic_negative | Figure: tree attention ablation | We fix beam length to 5, beam width to 45, and tune batch size to push the compute limit, Figure~\ref{fig:tree-attention-ablation} (right) shows that when the batch size is below 4, computational resources are abundan... |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of the acceptance prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 7 | attempted_not_committed | evidence-negative-quote-bank-quote-candidate-window-3-1 | quote-bank-negative-grounding_candidate | method_support_gap | insufficient_semantic_negative | Candidate negative window #3 | h hits the maximal generation length, we manually set $a = \Stop$.} We note that in an extended MDP setting, we can include the draft probability $q_{k+1}$ for the token $Y_{k+1}$ as a part of the current action. Fine... |
| cklg91aPGk | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-robustness-or-generaliza | stale_reviewer_absence_audit | missing_robustness_or_generalization |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing robustness or generalization concern; missing/mismatch item(s): evaluation on graph-level tasks (e.g., graph classification). Targ... |
| fGXyvmWpw6 | 4 | attempted_not_committed | evidence-3-turn-4 | not_verified_or_unknown | missing_analysis | insufficient_claim_relation | Ablation excerpt #1 | increasing number of local and global steps.} \label{fig:ablation} \end{figure} \subsection{Ablation studies for \ours{}} The success of \ours{} relies on the novel design of local-global data distillation, where the sel |
| fGXyvmWpw6 | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for local virtual data with regularization; observed inventory: Finally, after refining local and global virtual data $\tilde{D}^g$ and $\tilde{D}^c$, we continue federated virtual learning in stage 3 on local v... |
| fGXyvmWpw6 | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Ablation excerpt #1 | missing/mismatch: component-isolation ablation for federated gradient; observed inventory: increasing number of local and global steps.} \label{fig:ablation} \end{figure} \subsection{Ablation studies for \ours{}} The success of \ours{} re... |
| mHv6wcBb0z | 5 | attempted_not_committed | evidence-1-turn-4 | support_only | generic_gap |  | Figure 2 | For more details on the experimental setup and results, please refer to Section~\ref{sec: synthetic performance}. \begin{figure*}[h] |
| mHv6wcBb0z | 5 | attempted_not_committed | evidence-small-model-quote-bank-5-turn-4 | support_only | generic_gap |  | Figure: eignvalue in training | Figure \ref{fig: eignvalue_in_training} illustrates that during the initial training phase (100th epoch), the eigenvalues decay slowly for both DCCA and NR-DCCA. |
| mHv6wcBb0z | 6 | attempted_not_committed | evidence-1-turn-4 | support_only | generic_gap |  | Figure 2 | For more details on the experimental setup and results, please refer to Section~\ref{sec: synthetic performance}. \begin{figure*}[h] |
| mHv6wcBb0z | 6 | attempted_not_committed | evidence-small-model-quote-bank-5-turn-4 | support_only | generic_gap |  | Figure: eignvalue in training | Figure \ref{fig: eignvalue_in_training} illustrates that during the initial training phase (100th epoch), the eigenvalues decay slowly for both DCCA and NR-DCCA. |
| KOUAayk5Kx | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting baseline comparison for OGL-guided. Target claim: 'The proposed OGL-guide... |
| KOUAayk5Kx | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for orthogonal gradient; observed inventory: To overcome the issue, we propose an orthogonal gradient learning (OGL) guided supernet training paradigm for one-shot NAS, where the novelty lies ... |
