# Recovery Case Audit v1

## Summary

| metric | count |
| --- | --- |
| bucket::assessment_limitation_routing | 1 |
| bucket::attempted_not_committed | 14 |
| bucket::committed_not_effective | 6 |
| bucket::effective_repair_without_verified_negative | 2 |
| bucket::verified_review_issue_repair | 6 |
| case_rows | 29 |
| effective_repair_not_verified_negative_repair | 9 |
| effective_repair_turns | 9 |
| evidence_bucket::insufficient_claim_relation | 1 |
| evidence_bucket::missing_evidence_id | 1 |
| evidence_bucket::obligation_grounded_review_issue | 6 |
| evidence_bucket::quote-bank-negative-grounding_candidate | 2 |
| evidence_bucket::stale_reviewer_absence_audit | 3 |
| evidence_bucket::support_only | 2 |
| evidence_bucket::verified_review_negative | 1 |
| operation::mark_contested | 8 |
| operation::record_diagnosis_pending_concern | 4 |
| operation::reject_patch | 13 |
| operation::route_to_assessment_limitation | 3 |
| turns_with_verified_review_issue_bundle_evidence | 6 |
| turns_with_verified_review_negative_evidence | 1 |

## Recovery Cases

| paper_id | turn | bucket | operation | layer | target | status | evidence_buckets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | attempted_not_committed | reject_patch | attempted | claim:claim-1 | partially_supported->unsupported | {"quote-bank-negative-grounding_candidate": 1} |
| WNxlJJIEVj | 5 | attempted_not_committed |  |  | : | -> | {} |
| WNxlJJIEVj | 6 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| uOrfve3prk | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |
| uOrfve3prk | 7 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | partially_supported->unsupported | {"verified_review_negative": 1} |
| 7Dub7UXTXN | 4 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| 7Dub7UXTXN | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| 9zEBK3E9bX | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-2 | supported->unsupported | {"insufficient_claim_relation": 1} |
| XyB4VvF01X | 4 | assessment_limitation_routing | route_to_assessment_limitation | hygiene_delta_improved | flaw:flaw-reviewer-absence-claim-1-missing-ablation | candidate->downgraded | {"quote-bank-negative-grounding_candidate": 1} |
| XyB4VvF01X | 6 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-3 | open->recorded | {} |
| WpXq5n8yLb | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | partially_supported->partially_supported | {"obligation_grounded_review_issue": 1} |
| NnExMNiTHw | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | uncertain->unsupported | {} |
| NnExMNiTHw | 5 | attempted_not_committed | reject_patch | patch_validated | claim:claim-3 | uncertain->unsupported | {"stale_reviewer_absence_audit": 1} |
| fGXyvmWpw6 | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-1 | -> | {} |
| QAgwFiIY4p | 4 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-pst-counts-all-tested-subs | -> | {} |
| QAgwFiIY4p | 6 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-pst-counts-all-tested-subs | -> | {} |
| TPAj63ax4Y | 4 | attempted_not_committed | reject_patch | attempted | claim:claim-3 | supported->unsupported | {"missing_evidence_id": 1} |
| TPAj63ax4Y | 5 | effective_repair_without_verified_negative | mark_contested | hygiene_delta_improved | claim:claim-3 | supported->supported | {"stale_reviewer_absence_audit": 1} |
| mHv6wcBb0z | 4 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->retracted | {} |
| mHv6wcBb0z | 6 | committed_not_effective | route_to_assessment_limitation | patch_committed | flaw:flaw-1 | candidate->retracted | {} |
| xUe1YqEgd6 | 3 | attempted_not_committed | reject_patch | attempted | flaw:flaw-reviewer-absence-claim-2-missing-ablation | -> | {} |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| xUe1YqEgd6 | 5 | committed_not_effective | record_diagnosis_pending_concern | diagnosis_pending_recorded | claim_requirement_gap:claim-2 | open->recorded | {} |
| YXn76HMetm | 4 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| KOUAayk5Kx | 4 | attempted_not_committed | reject_patch | patch_validated | claim:claim-1 | unsupported->supported | {"support_only": 2} |
| KOUAayk5Kx | 5 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-1 | supported->supported | {"obligation_grounded_review_issue": 1} |
| KOUAayk5Kx | 6 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| KOUAayk5Kx | 7 | verified_review_issue_repair | mark_contested | hygiene_delta_improved | claim:claim-2 | supported->supported | {"obligation_grounded_review_issue": 1} |
| XH3OiIhtvf | 4 | attempted_not_committed | reject_patch | attempted | : | -> | {} |

## Evidence Details

| paper_id | turn | case_bucket | evidence_id | evidence_bucket | negative_type | review_label | locator | quote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | 6 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-2-1 | quote-bank-negative-grounding_candidate | scope_limitation | author_limitation_only | Limitation / Gap / Negative evidence excerpt #2 | Extending TCMT to address instantaneous causal relations and providing a better model of the auxiliary context variables are clear directions for future work. |
| WNxlJJIEVj | 6 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-1-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting comparison against high-retur. Target claim: 'The proposed CDiffuser meth... |
| uOrfve3prk | 7 | attempted_not_committed | evidence-2-turn-6 | verified_review_negative | evaluation_protocol_risk | review_negative_verified | Limitation / Gap / Negative evidence excerpt #3 | Note that $\alpha$ is a hyperparameter that must be tuned for each method, model, and sometimes even intervention feature and thus cannot be used to compare the effects of interventions across methods. |
| 9zEBK3E9bX | 4 | attempted_not_committed | evidence-targeted-candidate-quote-neg-search-quote-claim-2-negative-result-quote | insufficient_claim_relation | negative_result | insufficient_claim_relation | Section: 4.3 DISCUSSIONS AND ANALYSES | 5 reveal that relying solely on detection as a pre-training task yields minimal performance gains, particularly |
| XyB4VvF01X | 4 | assessment_limitation_routing | evidence-negative-quote-bank-quote-critique-negative-1-2 | quote-bank-negative-grounding_candidate | negative_result | insufficient_claim_relation | Limitation / Gap / Negative evidence excerpt #1 | The addition of names in G2T-Named-Update fares slightly worse than the main G2T solver G2T-Anon-Update. |
| WpXq5n8yLb | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for recurrent neural network; observed inventory: Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head. |
| NnExMNiTHw | 5 | attempted_not_committed | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline | insufficient_semantic_negative | comparison | We compare \ours with the naive speculative decoding algorithm where the number of the candidate tokens $K$ is fixed as a hyperparameter. We tune $K$ in \{2,4,6,8,10, 12, 14\}. |
| TPAj63ax4Y | 4 | attempted_not_committed | evidence-negative-quote-bank-quote-critique-negative-1-1 | missing_evidence_id |  |  |  |  |
| TPAj63ax4Y | 5 | effective_repair_without_verified_negative | evidence-reviewer-absence-claim-3-baseline-or-comparison-m | stale_reviewer_absence_audit | missing_baseline |  | claim-evidence coverage audit | Verified review issue bundle: the paper claim and observed inventory support a missing baseline concern; missing/mismatch item(s): same-setting baseline comparison for ZS-Our. Target claim: 'The proposed zero-shot met... |
| xUe1YqEgd6 | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper inventory #78 | missing/mismatch: component-isolation ablation for Divided attention; observed inventory: \section{5.1 ABLATION STUDY } We have conducted an ablation study to assess three main components of our method LT-MS with four masks $(K\,=\,4)$ )... |
| YXn76HMetm | 4 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-baseline-or-comparison-m | obligation_grounded_review_issue | missing_baseline | review_negative_absence_audit_verified | paper inventory #4 | missing/mismatch: same-setting comparison against paper-named EqualAL baseline; observed inventory: HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that ... |
| KOUAayk5Kx | 4 | attempted_not_committed | evidence-1-turn-3 | support_only | generic_gap |  | Section 3.1 | In order to handle the multi-model forgetting, we design an effective orthogonal gradient learning (OGL) for supernet training and meanwhile avoid the projector attenuation. The main idea is to design a gradient space |
| KOUAayk5Kx | 4 | attempted_not_committed | evidence-small-model-quote-bank-7-turn-3 | support_only | generic_gap |  | Lemma 2 | 3 can be obtained according to Lemma 2. Lemma 2. Given a gradient space $S_{r}^{(i,j)}$ consists of a number of gradient vectors, i.e., $S_{r}^{(i,j)}\,=$ $\{g_{1},g_{2},...,g_{n}\}$ , the projection of $\Delta w_{l,r}^{ |
| KOUAayk5Kx | 5 | verified_review_issue_repair | evidence-reviewer-absence-claim-1-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for orthogonal direction to the gradient; observed inventory: To overcome the issue, we propose an orthogonal gradient learning (OGL) guided supernet training paradigm for one-shot NAS, where the novelty lies ... |
| KOUAayk5Kx | 6 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for orthogonal gradient; observed inventory: To overcome the issue, we propose an orthogonal gradient learning (OGL) guided supernet training paradigm for one-shot NAS, where the novelty lies ... |
| KOUAayk5Kx | 7 | verified_review_issue_repair | evidence-reviewer-absence-claim-2-ablation-or-component-mi | obligation_grounded_review_issue | missing_ablation | review_negative_absence_audit_verified | paper component inventory #1 | missing/mismatch: component-isolation ablation for orthogonal gradient; observed inventory: To overcome the issue, we propose an orthogonal gradient learning (OGL) guided supernet training paradigm for one-shot NAS, where the novelty lies ... |
