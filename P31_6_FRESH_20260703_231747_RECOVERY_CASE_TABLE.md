# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 8 |
| bucket::committed_not_effective | 1 |
| bucket::effective_repair_without_verified_negative | 1 |
| bucket::verified_review_issue_repair | 8 |
| case_rows | 18 |
| effective_repair_not_verified_negative_repair | 9 |
| effective_repair_turns | 9 |
| evidence_bucket::obligation_grounded_review_issue | 8 |
| evidence_bucket::stale_reviewer_absence_audit | 1 |
| operation::mark_contested | 9 |
| operation::record_diagnosis_pending_concern | 1 |
| operation::reject_patch | 6 |
| turns_with_verified_review_issue_bundle_evidence | 8 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| ye3NrNrYOY | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| 9zEBK3E9bX | 3 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | -> | {} |
| XyB4VvF01X | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| XyB4VvF01X | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| GE6iywJtsV | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-insufficient-baseline-detail | -> | {} |
| WpXq5n8yLb | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| a6SntIisgg | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| a6SntIisgg | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| fGXyvmWpw6 | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | -> | {} |
| QAgwFiIY4p | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| mHv6wcBb0z | 5 | attempted_not_committed |  |  | : | -> | {} |
| mHv6wcBb0z | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| YXn76HMetm | 6 | attempted_not_committed |  |  | : | -> | {} |
| KOUAayk5Kx | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XyB4VvF01X | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Comparison / Robustness excerpt #1 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: Proof State Text-based Transformer We implement a decoder-only transformer baseline that operates on the textual representations of the proof state... |
| XyB4VvF01X | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-efficiency-cost-efficien | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the eff... |
| WpXq5n8yLb | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| NnExMNiTHw | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for of our trained prediction head; observed inventory: We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens. |
| a6SntIisgg | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for Global Encoder; observed inventory: To address this issue, we propose the \textbf{Lo}cal-\textbf{G}l\textbf{o}bal \textbf{R}epresentation \textbf{A}lignment framework (\abbr), which e... |
| a6SntIisgg | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for Global Encoder; observed inventory: To address this issue, we propose the \textbf{Lo}cal-\textbf{G}l\textbf{o}bal \textbf{R}epresentation \textbf{A}lignment framework (\abbr), which e... |
| QAgwFiIY4p | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | paper inventory #2 | missing/mismatch: runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficie...; observed inventory: Extensive experiments further validate PST's outstanding real-world performance. |
| mHv6wcBb0z | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for with a generalized noise regularization; observed inventory: Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach. |
