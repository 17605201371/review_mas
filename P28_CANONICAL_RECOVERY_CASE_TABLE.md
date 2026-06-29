# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 16 |
| bucket::committed_not_effective | 2 |
| bucket::effective_repair_without_verified_negative | 8 |
| bucket::verified_review_issue_repair | 4 |
| case_rows | 30 |
| effective_repair_not_verified_negative_repair | 12 |
| effective_repair_turns | 12 |
| evidence_bucket::author_limitation_only | 3 |
| evidence_bucket::obligation_grounded_review_issue | 5 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 5 |
| evidence_bucket::stale_reviewer_absence_audit | 9 |
| evidence_bucket::support_only | 2 |
| operation::mark_contested | 12 |
| operation::reject_patch | 15 |
| operation::route_to_assessment_limitation | 2 |
| turns_with_verified_review_issue_bundle_evidence | 4 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-ablation | -> | {} |
| uOrfve3prk | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| 7Dub7UXTXN | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| 9zEBK3E9bX | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| 9zEBK3E9bX | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| XyB4VvF01X | 5 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-2-missing-ablation | candidate->retracted | {"stale_reviewer_absence_audit": 1} |
| XyB4VvF01X | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| XyB4VvF01X | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| GE6iywJtsV | 6 | attempted_not_committed |  |  | : | -> | {} |
| WpXq5n8yLb | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-reviewer-absence-claim-3-efficiency-cost-gap | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| NnExMNiTHw | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | -> | {} |
| a6SntIisgg | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| a6SntIisgg | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| a6SntIisgg | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 3 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | partially_supported->unsupported | {"author_limitation_only": 1} |
| fGXyvmWpw6 | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 2} |
| fGXyvmWpw6 | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | partially_supported->unsupported | {"author_limitation_only": 1} |
| fGXyvmWpw6 | 6 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | uncertain->unsupported | {"author_limitation_only": 1} |
| fGXyvmWpw6 | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-baseline | -> | {} |
| QAgwFiIY4p | 5 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| mHv6wcBb0z | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | uncertain->supported | {"support_only": 2} |
| mHv6wcBb0z | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| xUe1YqEgd6 | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| YXn76HMetm | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-3-missing-baseline | candidate->retracted | {} |
| YXn76HMetm | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| KOUAayk5Kx | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 7 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| uOrfve3prk | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for decoder. Target claim: 'The paper proposes a unified ... |
| 7Dub7UXTXN | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for is trained with full-batch gradient. Target claim: 'F... |
| 9zEBK3E9bX | 5 | attempted_not_committed | evidence-negative-quote-bank-quote-theory-or-proof-1-2 | quote-bank-negative-grounding_candidate | scope_limitation | insufficient_semantic_negative | Theory / Proof excerpt #1 | The proposed SPOT focuses on learning general representations via occupancy prediction task, achieving both task- and dataset-level generalization. Besides, SPOT achieves scalable performance gains across different datas |
| 9zEBK3E9bX | 6 | attempted_not_committed | evidence-negative-quote-bank-quote-theory-or-proof-1-2 | quote-bank-negative-grounding_candidate | scope_limitation | insufficient_semantic_negative | Theory / Proof excerpt #1 | The proposed SPOT focuses on learning general representations via occupancy prediction task, achieving both task- and dataset-level generalization. Besides, SPOT achieves scalable performance gains across different datas |
| XyB4VvF01X | 5 | attempted_not_committed | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for predicts a textual representation. Target claim: 'Gra... |
| XyB4VvF01X | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for predicts a textual representation. Target claim: 'Gra... |
| XyB4VvF01X | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for predicts a textual representation. Target claim: 'Gra... |
| WpXq5n8yLb | 4 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-2-3 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | Despite the limited compute resources in this setup, we observed a memory bottleneck. |
| a6SntIisgg | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-2-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for convolutional network. Target claim: 'The method uses... |
| a6SntIisgg | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for convolutional network. Target claim: 'The paper propo... |
| a6SntIisgg | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for convolutional network. Target claim: 'The paper propo... |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting baseline comparison for local-global. Target claim: 'Ablation studies dem... |
| cklg91aPGk | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #5 | missing/mismatch: recent GNN or graph-transformer baselines on the same graph benchmarks; observed inventory: By leveraging the inherent structural information in graphs, GCL has achieved state-of-the-art performance on graph learning tasks (Velickovic et a... |
| fGXyvmWpw6 | 3 | attempted_not_committed | quote-critique-negative-1 | author_limitation_only | negative_result | author_limitation_only | Figure: condensed tsne | Worse yet, we found increased data heterogeneity among clients when federatively training with distilled local virtual data (see Figure~\ref{fig:condensed_tsne}). |
| fGXyvmWpw6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #9 | missing/mismatch: same-setting baseline comparison for Local-global; observed inventory: Our method outperforms \textit{state-of-the-art} heterogeneous FL algorithms under various settings with a very limited amount of distilled virtual... |
| fGXyvmWpw6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for local virtual data with regularization; observed inventory: Finally, after refining local and global virtual data $\tilde{D}^g$ and $\tilde{D}^c$, we continue federated virtual learning in stage 3 on local v... |
| fGXyvmWpw6 | 5 | attempted_not_committed | evidence-critique-negative-1 | author_limitation_only | negative_result | author_limitation_only | Figure: condensed tsne | Such heterogeneity will degrade the performance of FL. Worse yet, we found increased data heterogeneity among clients when federatively training with distilled local virtual data (see Figure~\ref{fig:condensed_tsne}). |
| fGXyvmWpw6 | 6 | attempted_not_committed | evidence-critique-negative-1 | author_limitation_only | negative_result | author_limitation_only | Figure: condensed tsne | Such heterogeneity will degrade the performance of FL. Worse yet, we found increased data heterogeneity among clients when federatively training with distilled local virtual data (see Figure~\ref{fig:condensed_tsne}). |
| QAgwFiIY4p | 5 | committed_not_effective | evidence-negative-quote-bank-quote-table-or-figure-1-2 | quote-bank-negative-grounding_candidate | scope_limitation | positive_or_neutral_support | Table/Figure caption: Results on graph property prediction tasks. | without Euclidean distance also outperforms baselines on 6 out of 12 targets. \begin{table}[t] \vskip -7pt \caption{Results on graph property prediction tasks.}\label{tab::zinc} \vskip 7pt \centering \setlength{\tabcolse |
| mHv6wcBb0z | 4 | attempted_not_committed | evidence-1-turn-3 | support_only | generic_gap |  | Comparison / Robustness excerpt #1 | Our proposed NR-DCCA achieves state-of-the-art performance as well as training stability to prevent model collapse. |
| mHv6wcBb0z | 4 | attempted_not_committed | evidence-small-model-quote-bank-4-turn-3 | support_only | generic_gap |  | Table/Figure caption: Eigenvalue distributions of the first linear layer's weight matrices in | distributions. In our primary experiments, we utilize Gaussian white noise. \begin{figure}[h] \centering \includegraphics[width=0.8\linewidth]{figures/creatation_bechmarks.png} \caption{Construction of a synthetic datase |
| mHv6wcBb0z | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
| KOUAayk5Kx | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #5 | missing/mismatch: same-setting baseline comparison for OGL-guided; observed inventory: Besides, we apply the proposed paradigm to two one-shot NAS baselines, and experimental results have demonstrated that our approach is able to miti... |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-negative-quote-bank-quote-claim-match-2-2 | quote-bank-negative-grounding_candidate | scope_limitation | positive_or_neutral_support | Section 3 | This visual representation demonstrates a significant improvement in EER when transitioning from individual models to federated models without a secure aggregator in the unsupervised system. |
