# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 2 |
| bucket::verified_review_issue_repair | 5 |
| case_rows | 7 |
| effective_repair_not_verified_negative_repair | 5 |
| effective_repair_turns | 5 |
| evidence_bucket::obligation_grounded_review_issue | 6 |
| operation::mark_contested | 5 |
| operation::reject_patch | 1 |
| turns_with_verified_review_issue_bundle_evidence | 6 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GE6iywJtsV | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| GE6iywJtsV | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| QAgwFiIY4p | 5 | attempted_not_committed |  |  | : | -> | {} |
| QAgwFiIY4p | 7 | attempted_not_committed | reject_patch | patch_validated | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"obligation_grounded_review_issue": 1} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GE6iywJtsV | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Claim-matched evidence excerpt #1 | missing/mismatch: graph control module; component-isolation ablation for with a graph control module; observed inventory: In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it composed an unconditioned... |
| GE6iywJtsV | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: consisting of a constrain module; observed inventory: Inspired by the well-known ControlNet for conditioned image generation, supposing an unconditioned 3D molecule generative model was already trained... |
| NnExMNiTHw | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Comparison / Robustness excerpt #1 | missing/mismatch: acceptance prediction head; component-isolation ablation for trained acceptance prediction head; observed inventory: Compared with the baseline speculative decoding (SpecDec) with fixed candidate lengths, by adaptively determining the candidate lengths via a train... |
| NnExMNiTHw | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | Section: SpecDec++: Theory and Algorithm | missing/mismatch: acceptance prediction head; observed inventory: Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \... |
| QAgwFiIY4p | 7 | attempted_not_committed | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #11 | missing/mismatch: same-setting comparison against paper-named Graphormer baseline; observed inventory: Extensive experiments verify these claims across synthetic datasets, graph property prediction datasets, and long-range graph benchmarks. Specifica... |
| YXn76HMetm | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | Table: main ablation | missing/mismatch: same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO demonstrates a substantial improvement of +10.4\% compared to methods (a) and (b) in Table \ref{tab:main-ablation}. |
