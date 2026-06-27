# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::attempted_not_committed | 15 |
| bucket::committed_not_effective | 6 |
| bucket::effective_repair_without_verified_negative | 3 |
| bucket::verified_review_issue_repair | 3 |
| case_rows | 27 |
| effective_repair_not_verified_negative_repair | 6 |
| effective_repair_turns | 6 |
| evidence_bucket::insufficient_claim_relation | 1 |
| evidence_bucket::missing_evidence_id | 3 |
| evidence_bucket::not_verified_or_unknown | 1 |
| evidence_bucket::obligation_grounded_review_issue | 3 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 2 |
| evidence_bucket::stale_reviewer_absence_audit | 6 |
| operation::mark_contested | 6 |
| operation::record_diagnosis_pending_concern | 3 |
| operation::reject_patch | 13 |
| operation::route_to_assessment_limitation | 3 |
| turns_with_verified_review_issue_bundle_evidence | 3 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| WNxlJJIEVj | 5 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-scope-overclaim | -> | {} |
| uOrfve3prk | 5 | attempted_not_committed |  |  | : | -> | {} |
| 7Dub7UXTXN | 7 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| XyB4VvF01X | 3 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 1} |
| XyB4VvF01X | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | partially_supported->unsupported | {"insufficient_claim_relation": 1} |
| XyB4VvF01X | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-1-missing-ablation | -> | {} |
| GE6iywJtsV | 5 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-reviewer-absence-claim-2-missing-ablation | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| NnExMNiTHw | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-insufficient-evaluation | -> | {} |
| a6SntIisgg | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| a6SntIisgg | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-baseline | -> | {} |
| cklg91aPGk | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-1 | open->recorded | {} |
| HPuLU6q7xq | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| HPuLU6q7xq | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-3-missing-ablation | candidate->downgraded | {"missing_evidence_id": 1} |
| fGXyvmWpw6 | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-reviewer-absence-claim-1-missing-ablation | candidate->downgraded | {"missing_evidence_id": 1} |
| fGXyvmWpw6 | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | partially_supported->unsupported | {"missing_evidence_id": 1} |
| fGXyvmWpw6 | 7 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | partially_supported->partially_supported | {"stale_reviewer_absence_audit": 2} |
| QAgwFiIY4p | 3 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1, "stale_reviewer_absence_audit": 1} |
| TPAj63ax4Y | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| TPAj63ax4Y | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| TPAj63ax4Y | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-3 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-2 | candidate->confirmed | {"not_verified_or_unknown": 1} |
| YXn76HMetm | 5 | attempted_not_committed |  |  | : | -> | {} |
| YXn76HMetm | 6 | attempted_not_committed | reject_patch | patch_validated | flaw:flaw-reviewer-absence-claim-2-insufficient-evaluation | candidate->downgraded | {"stale_reviewer_absence_audit": 1} |
| YXn76HMetm | 7 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-ablation | -> | {} |
| KOUAayk5Kx | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-3-missing-ablation | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9zEBK3E9bX | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-efficiency-cost-efficien | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, or hardware measurement for pre-training. Target ... |
| XyB4VvF01X | 3 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for Graph2Tac. Target claim: 'Graph2Tac introduces a nove... |
| XyB4VvF01X | 5 | attempted_not_committed | evidence-critique-negative-1 | insufficient_claim_relation | negative_result | insufficient_claim_relation | Limitation / Gap / Negative evidence excerpt #1 | The addition of names in G2T-Named-Update fares slightly worse than the main G2T solver G2T-Anon-Update. |
| GE6iywJtsV | 5 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-1-1 | quote-bank-negative-grounding_candidate | negative_result | insufficient_claim_relation | Figure 4 | It is even worse for the best ones with a median of |
| HPuLU6q7xq | 6 | attempted_not_committed | evidence-reviewer-absence-claim-3-ablation-or-component-mi | missing_evidence_id |  |  |  |  |
| fGXyvmWpw6 | 4 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-2-4 | missing_evidence_id |  |  |  |  |
| fGXyvmWpw6 | 6 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-3-1 | missing_evidence_id |  |  |  |  |
| fGXyvmWpw6 | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-ablation-or-component-mi | stale_reviewer_absence_audit | missing_ablation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing ablation concern; missing/mismatch item(s): component-isolation ablation for local-global. Target claim: 'The paper proposes a loc... |
| fGXyvmWpw6 | 7 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-efficiency-cost-efficien | stale_reviewer_absence_audit | efficiency_cost_gap |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a efficiency cost gap concern; missing/mismatch item(s): runtime, memory, parameter, FLOP, or hardware measurement for local-global. Target ... |
| QAgwFiIY4p | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-scope-coverage-scope-ove | stale_reviewer_absence_audit | scope_overclaim |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a scope overclaim concern; missing/mismatch item(s): held-out or coverage evaluation for GNNs. Target claim: 'The conversion method enables ... |
| QAgwFiIY4p | 3 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-efficiency-cost-efficien | obligation_grounded_review_issue | efficiency_cost_gap | review_negative_absence_audit_verified | Table/Figure caption: Results on graph property prediction tasks. | missing/mismatch: parameter measurement under the claimed setting; observed inventory: \caption{Results on graph property prediction tasks.}\label{tab::zinc} |
| TPAj63ax4Y | 4 | committed_not_effective | evidence-negative-quote-bank-quote-critique-negative-1-3 | quote-bank-negative-grounding_candidate | scope_overclaim | author_limitation_only | Limitation / Gap / Negative evidence excerpt #1 | One of the limitations of our method is the class projection mechanism used in Stage 1, which requires one to know \textit{a priori} at least the general types of objects that will be encountered. |
| TPAj63ax4Y | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #4 | missing/mismatch: same-setting comparison against LAVT; observed inventory: In our experiments, using only the first two steps (zero-shot segment and select) outperforms other zero-shot baselines by as much as 16.5\%, while... |
| TPAj63ax4Y | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #4 | missing/mismatch: same-setting comparison against LAVT; observed inventory: In our experiments, using only the first two steps (zero-shot segment and select) outperforms other zero-shot baselines by as much as 16.5\%, while... |
| xUe1YqEgd6 | 7 | attempted_not_committed | evidence-critique-negative-2 | not_verified_or_unknown | negative_result | insufficient_paper_grounding | Table 2 | For LT-MS-K4... Jaccard index 0.61... Unsupervised method (score) 0.63 |
| YXn76HMetm | 6 | attempted_not_committed | evidence-reviewer-absence-claim-2-empirical-result-insuffi | stale_reviewer_absence_audit | insufficient_evaluation |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a insufficient evaluation concern; missing/mismatch item(s): quantitative result table or metric for pixel-level. Target claim: 'Using epist... |
