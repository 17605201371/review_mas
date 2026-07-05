# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 12 |
| bucket::committed_not_effective | 3 |
| bucket::verified_review_issue_repair | 16 |
| case_rows | 31 |
| effective_repair_not_verified_negative_repair | 16 |
| effective_repair_turns | 16 |
| evidence_bucket::not_verified_or_unknown | 1 |
| evidence_bucket::obligation_grounded_review_issue | 17 |
| evidence_bucket::support_only | 1 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 16 |
| operation::record_diagnosis_pending_concern | 3 |
| operation::reject_patch | 11 |
| turns_with_verified_review_issue_bundle_evidence | 16 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WNxlJJIEVj | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| uOrfve3prk | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| 7Dub7UXTXN | 5 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| GE6iywJtsV | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
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
| QAgwFiIY4p | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| TPAj63ax4Y | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| mHv6wcBb0z | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 2} |
| mHv6wcBb0z | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-4 | supported->supported | {"obligation_grounded_review_issue": 1} |
| mHv6wcBb0z | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-5 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-1 | candidate->candidate | {"verified_review_negative": 1} |
| XH3OiIhtvf | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | candidate->confirmed | {"not_verified_or_unknown": 1, "support_only": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Conclusion / Discussion excerpt #1 | missing/mismatch: in causal representation; observed inventory: \section{5 CONCLUSION } We propose Temporal Causal Mechanism Transfer (TCMT) for few-shot action recognition, which relies on variational inference... |
| 9zEBK3E9bX | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: unified 3D scene representation; observed inventory: In this paper, SPOT is proposed to use 3D semantic occupancy prediction to learn a unified 3D scene |
| GE6iywJtsV | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: pockets with the GLIDE module; observed inventory: tions and templates, while the 3D shape similarity was calculated with the ROCS software of OE Toolkit package in default settings.30(Grant et al.,... |
| GE6iywJtsV | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: pockets with the GLIDE module; observed inventory: tions and templates, while the 3D shape similarity was calculated with the ROCS software of OE Toolkit package in default settings.30(Grant et al.,... |
| WpXq5n8yLb | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: from LLMs improves the alignment; observed inventory: \cmnt{This approach is taken because LLM occasionally produces unreasonable predictions in long sequences.} \section{Experiment} We conduct experim... |
| WpXq5n8yLb | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for from LLMs improves the alignment; observed inventory: \cmnt{This approach is taken because LLM occasionally produces unreasonable predictions in long sequences.} \section{Experiment} We conduct experim... |
| NnExMNiTHw | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-5-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: SpecDec++: Theory and Algorithm | missing/mismatch: our trained prediction head; observed inventory: Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \... |
| fGXyvmWpw6 | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when t... |
| QAgwFiIY4p | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Section: Long Range Graph Benchmark | missing/mismatch: same-setting comparison against paper-named Graphormer baseline; observed inventory: PST outperforms all baselines on the PascalVOC-SP and Peptides-Func datasets and achieves the third-highest performance on the Peptides-Struct data... |
| TPAj63ax4Y | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: same-setting comparison against paper-named CLIP baseline; observed inventory: However, while collecting referred annotation masks is a time-consuming process, the few existing weakly-supervised and zero-shot approaches fall s... |
| mHv6wcBb0z | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section 3.2 | missing/mismatch: ablation isolating proposed Noise Regularization module; observed inventory: parentheses next to the dataset name.} \label{fig: real_world_cca} \end{figure} \section{Conclusions} We propose a novel noise regularization appro... |
| mHv6wcBb0z | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: same-setting comparison against paper-named MVTCAE baseline; observed inventory: Deep Canonical Correlation Analysis (DCCA) and its variants share simple formulations and demonstrate state-of-the-art performance. |
| mHv6wcBb0z | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-4-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section 3 | missing/mismatch: component-isolation ablation for Noise Regularization; observed inventory: obtained directly using $\{f_k^*\}_k$ in the same manner as DCCA. \subsection{Theoretical Analysis} In this section, we provide the rationale for w... |
| mHv6wcBb0z | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #1 | missing/mismatch: same-setting comparison against paper-named MVTCAE baseline; observed inventory: Deep Canonical Correlation Analysis (DCCA) and its variants share simple formulations and demonstrate state-of-the-art performance. |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table: results table | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: For GTAV$\rightarrow$CS and CS$\rightarrow$ACDC, the mIoU is calculated on the shared 19 classes, whereas for SYNTHIA$\rightarrow$CS two mIoU value... |
| YXn76HMetm | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-5-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #3 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| XH3OiIhtvf | 6 | attempted_not_committed | evidence-critique-negative-1 | verified_review_negative | negative_result | review_negative_verified | Comparison Section / Table 1 | incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table. |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-1 | support_only | generic_gap | insufficient_paper_grounding | Fig. 2 | In contrast to the results shown in Fig. 2 (b), this highlights the crucial need to carefully evaluate the impact of a secure aggregator on EER results, indicating a possible trade-off between privacyenhancing measures |
| XH3OiIhtvf | 7 | attempted_not_committed | evidence-2 | not_verified_or_unknown | direct_contradiction | not_negative_evidence | Table 1 | Table 1 shows EER for 'Secure Aggregator' is 0.1586, which is higher (worse) than the 'Baseline' EER of 0.0612, contradicting the claim of improvement. |
