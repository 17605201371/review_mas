# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 12 |
| bucket::committed_not_effective | 1 |
| bucket::effective_repair_without_verified_negative | 2 |
| bucket::verified_review_issue_repair | 14 |
| case_rows | 29 |
| effective_repair_not_verified_negative_repair | 16 |
| effective_repair_turns | 16 |
| evidence_bucket::not_verified_or_unknown | 1 |
| evidence_bucket::obligation_grounded_review_issue | 14 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 2 |
| evidence_bucket::stale_reviewer_absence_audit | 3 |
| evidence_bucket::support_only | 3 |
| operation::mark_contested | 16 |
| operation::record_diagnosis_pending_concern | 1 |
| operation::reject_patch | 11 |
| turns_with_verified_review_issue_bundle_evidence | 14 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| uOrfve3prk | 7 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| 9zEBK3E9bX | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | supported->supported | {"support_only": 3} |
| 9zEBK3E9bX | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| XyB4VvF01X | 3 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| GE6iywJtsV | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | partially_supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| WpXq5n8yLb | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| WpXq5n8yLb | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| a6SntIisgg | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| cklg91aPGk | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| HPuLU6q7xq | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| HPuLU6q7xq | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| HPuLU6q7xq | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| QAgwFiIY4p | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| TPAj63ax4Y | 6 | attempted_not_committed |  |  | : | -> | {} |
| xUe1YqEgd6 | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-3 | partially_supported->unsupported | {"not_verified_or_unknown": 1} |
| xUe1YqEgd6 | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-robustness-or-ge | candidate->confirmed | {"stale_reviewer_absence_audit": 1} |
| xUe1YqEgd6 | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-robustness-or-ge | -> | {} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Limitation / Gap / Negative evidence excerpt #1 | missing/mismatch: fixed module; ablation isolating encoder/backbone or its named component; ablation isolating aspects of the causal mechanism module; observed inventory: We run an ablation study to select the hyperparameters of our model. We compare ${\mathrm{TCMT}}_{C}$ with the different numbers of latent causal v... |
| 9zEBK3E9bX | 5 | attempted_not_committed | evidence-1-turn-3 | support_only | generic_gap |  | Claim-matched evidence excerpt #2 | The goal of pre-training is to learn general representations for various downstream tasks, datasets, and architectures. In this section, we design extensive experiments to answer the question whether SPOT learns such |
| 9zEBK3E9bX | 5 | attempted_not_committed | evidence-small-model-quote-bank-4-turn-3 | support_only | generic_gap |  | Theory / Proof excerpt #1 | The proposed SPOT focuses on learning general representations via occupancy prediction task, achieving both task- and dataset-level generalization. Besides, SPOT achieves scalable performance gains across different datas |
| 9zEBK3E9bX | 5 | attempted_not_committed | evidence-claim-1-1 | support_only | generic_gap |  | Theory / Proof excerpt #1 | The proposed SPOT focuses on learning general representations via occupancy prediction task, achieving both task- and dataset-level generalization. Besides, SPOT achieves scalable performance gains across different datas |
| GE6iywJtsV | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Claim-matched evidence excerpt #1 | missing/mismatch: graph control module; component-isolation ablation for with a graph control module; observed inventory: In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it composed an unconditioned... |
| WpXq5n8yLb | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-2-1 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | Despite the limited compute resources in this setup, we observed a memory bottleneck. |
| WpXq5n8yLb | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| WpXq5n8yLb | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Comparison / Robustness excerpt #1 | missing/mismatch: component-isolation ablation for trained acceptance prediction head; observed inventory: Compared with the baseline speculative decoding (SpecDec) with fixed candidate lengths, by adaptively determining the candidate lengths via a train... |
| NnExMNiTHw | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: SpecDec++: Theory and Algorithm | missing/mismatch: acceptance prediction head; observed inventory: Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \... |
| a6SntIisgg | 4 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): feature dependencies by self-attention mechanism. Target claim: 'LogoRA introduces a n... |
| a6SntIisgg | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for feature dependencies by self-attention mechanism. Tar... |
| HPuLU6q7xq | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table/Figure caption: Basic statistics for OrcaData. | missing/mismatch: same-setting comparison against paper-named GPT-4 baseline; observed inventory: the agent's psychological activities and personality traits.} \end{figure} \begin{table}[ht] \centering \begin{minipage}{0.45\textwidth} \centering... |
| HPuLU6q7xq | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for modeling coarse and fine-grained fusion; observed inventory: For the coarse-grained model, we train the model by splicing personality trait reports into queries. |
| HPuLU6q7xq | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for modeling coarse and fine-grained fusion; observed inventory: For the coarse-grained model, we train the model by splicing personality trait reports into queries. |
| fGXyvmWpw6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Table/Figure excerpt #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: updating. On the contrary, we update our global virtual data during FL training. \begin{table}[t] \centering \caption{Averaged test accuracy for \t... |
| fGXyvmWpw6 | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Table/Figure excerpt #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: updating. On the contrary, we update our global virtual data during FL training. \begin{table}[t] \centering \caption{Averaged test accuracy for \t... |
| QAgwFiIY4p | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-1-1 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #1 | To overcome this, acceleration techniques such as sparse attention and linear attention could be explored, which will be our future work. |
| QAgwFiIY4p | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: Conclusion | missing/mismatch: y coordinates without information loss; observed inventory: We introduce a novel approach employing symmetric rank decomposition to transform interconnected nodes in graph into independent points with coordi... |
| QAgwFiIY4p | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: Conclusion | missing/mismatch: y coordinates without information loss; observed inventory: We introduce a novel approach employing symmetric rank decomposition to transform interconnected nodes in graph into independent points with coordi... |
| xUe1YqEgd6 | 4 | attempted_not_committed | evidence-critique-negative-1 | not_verified_or_unknown | missing_robustness_or_generalization | insufficient_paper_grounding | Section 5, Ablation Study, Table 2 caption | ated on the DAVIS2016 training set. ... comparative experiments on four datasets: DAVIS 2016, SegTrackV2, FBMS59, and DAVIS2017-motion. |
| xUe1YqEgd6 | 5 | attempted_not_committed | evidence-reviewer-absence-claim-3-robustness-or-generaliza | stale_reviewer_absence_audit | missing_robustness_or_generalization |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing robustness or generalization concern; missing/mismatch item(s): held-out or coverage evaluation for cross-dataset; held-out or cov... |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table: results table | missing/mismatch: same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL baseline; observed inventory: approach on a novel dataset, as shown in Table \ref{tab:results_table}c. \subsection{Ablation study} \label{sec:ablation} \input{tables/ablation_ta... |
