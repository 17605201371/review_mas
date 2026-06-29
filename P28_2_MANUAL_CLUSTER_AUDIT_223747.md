# P28.2 Manual Cluster Audit for 223747

- Source run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260629_223747.jsonl`
- Previous checkpoint: `P28_1_FIX_RECOMPUTE_223747_*`
- Current checkpoint: `P28_2_MANUALAUDIT_RECOMPUTE_223747_*`

## Summary

P28.1 had protection PASS and 10 verified review issue clusters, but manual inspection found four clusters that should not be paper-facing verified issues. P28.2 adds precision guards for those patterns and recomputes the same run.

P28.2 metrics:

- Overall protection: PASS
- `verified_review_issue_count=8`
- `verified_review_issue_cluster_count=6`
- `reviewer_candidate_review_issue_cluster_count=5`
- `claim_obligation_review_issue_cluster_count=0`
- `review_negative_verified_count=1`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- `semantic_negative_without_review_relation_count=0`
- `mark_contested_commit_count=8`
- `recovery_case_verified_review_issue_repair=2`

Interpretation: P28.2 is a precision checkpoint, not a quantity win. It gives a cleaner lower-bound set of review-worthy clusters, but the count is not yet enough for a strong quantity claim.

## Cluster Labels

| paper_id | cluster target | issue type | P28.2 status | manual label | judgment |
| --- | --- | --- | --- | --- | --- |
| `uOrfve3prk` | alpha tuning protocol caveat | `evaluation_protocol_risk` | retained | A | Direct quote says alpha must be tuned per method/model/feature and cannot compare intervention effects across methods. This is a real quote-grounded protocol caveat. |
| `NnExMNiTHw` | `acceptance_prediction_head` | `missing_ablation` | retained | A | The acceptance prediction head is a central claimed mechanism and no ablation section was found. Missing component isolation is review-worthy. |
| `YXn76HMetm` | `equalal_baseline` | `missing_baseline` | retained | A/B | EqualAL is a paper-named active-learning semantic-segmentation baseline in related work. Omission from same-setting comparison is a defensible reviewer issue. |
| `WpXq5n8yLb` | `recurrent_draft_model` | `missing_ablation` | retained | B | RNN draft model is one of the claimed performance drivers. Paper ablates dynamic tree attention and distillation, but not the RNN draft-model choice itself. |
| `mHv6wcBb0z` | `generalized_noise_regularization` | `missing_ablation` | retained | B | Generalized noise regularization is the named collapse-prevention mechanism. No direct component-isolation ablation was found in the inspected text. |
| `QAgwFiIY4p` | implementation reproducibility details | `reproducibility_gap` | retained | B/C | The SRD/PSRD transformation is central and complex. Some theory/implementation text exists, but deterministic protocol/hyperparameter details remain a defensible reproducibility concern. |
| `fGXyvmWpw6` | `local_virtual_data_regularization` | `missing_ablation` | rejected | D | Full text includes ablation studies for regularization loss/weighting and an `ours without regularization` comparison. This is counterevidence to a missing-regularization ablation claim. |
| `QAgwFiIY4p` | additional benchmark dataset matching claim scope | `missing_robustness_or_generalization` | rejected | D | Target is generic and does not name a concrete dataset/domain/protocol. It should stay diagnosis-pending, not verified. |
| `xUe1YqEgd6` | `divided_attention` | `missing_ablation` | rejected | D | `Divided attention` refers to prior-work DivA, not an LT-MS component. LT-MS has its own three-component ablation; the target is off-paper/off-claim. |
| `KOUAayk5Kx` | `orthogonal_gradient_learning` | `missing_ablation` | rejected | D | Paper reports RandomNAS/GDAS vs RandomNAS-OGL/GDAS-OGL and with/without OGL comparisons. Those are counterevidence to a missing OGL ablation claim. |

## Guards Added From Audit

- Missing-ablation target must be bound to current-paper claim/inventory context, preventing prior-work component names from becoming current-paper missing ablations.
- Explicit `with/without <target>` comparisons count as ablation counterevidence even when the paper does not use the word `ablation`.
- Regularization ablation text such as `without regularization` or `regularization loss/weight` resolves missing-regularization ablation claims.
- Generic robustness targets such as `additional benchmark dataset matching the claim scope` are not concrete enough for verified review issues.

## Next Step

Do not relax these guards to restore count. The next quantity work should increase reviewer-candidate recall for concrete, paper-bound issues while preserving the same verifier boundary. The current P28.2 result is a clean lower bound: 6 system-clustered review-worthy issues from hardneg20 after protection and manual-audit-driven precision fixes.
