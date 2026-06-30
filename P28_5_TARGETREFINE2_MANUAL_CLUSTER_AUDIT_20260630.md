# P28.5 TargetRefine2 Manual Cluster Audit

Date: 2026-06-30

Scope: `P28_5_TARGETREFINE2_194911_*`, offline recompute over the fresh MiMo hardneg20 run `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260630_194911.jsonl`.

## Headline

P28.5 TargetRefine2 is a precision checkpoint. It should be reported as:

- 13 verifier-passing review issue rows
- 9 deduplicated verified review issue clusters
- 0 direct quote-grounded review negatives
- 14 non-destructive `mark_contested` commits in the live run, but only 6 remain verified-review-issue repairs after offline verifier tightening; the rest are stale absence repairs caused by using stricter code after the API run
- Protection PASS: no unlinked negative evidence, no semantic negative without review relation, no positive/neutral negative candidate

Do not report the earlier fresh raw count of 22 rows / 16 clusters as the final result. TargetRefine2 deliberately removes generic or malformed missing-ablation targets such as action-representation fragments, bare fusion, bare federated gradient, loss expectation fragments, and generic deep neural network training.

## Manual Cluster Labels

| paper_id | cluster target | type | label | note |
| --- | --- | --- | --- | --- |
| 9zEBK3E9bX | class-balancing_cross_entropy_loss | missing_ablation | B | Specific component-level training/loss mechanism; defensible if no isolated ablation covers class-balancing CE. |
| GE6iywJtsV | implementation_reproducibility_details | reproducibility_gap | B | Concrete GrCN/ControllNet reproducibility issue; useful but should not be overstated as a decisive reject flaw. |
| WpXq5n8yLb | recurrent_draft_model | missing_ablation | A | Core ReDrafter mechanism; missing isolation is a strong reviewer issue. |
| NnExMNiTHw | acceptance_prediction_head | missing_ablation | A | Core SpecDec++ mechanism; cluster includes BCE/head-related rows and should be counted once. |
| cklg91aPGk | transformation_phase_weights_propgcl | missing_ablation | B | Specific efficiency/mechanism issue from Critique payload; wording is awkward but review-worthy. |
| cklg91aPGk | recent_gnn_graph-transformer_baselines | missing_baseline | B | Defensible baseline coverage issue, but target family remains broader than a named missing method. |
| mHv6wcBb0z | generalized_noise_regularization | missing_ablation | A | Named contribution mechanism; strong missing-ablation issue. |
| xUe1YqEgd6 | number_motion_components_beyond | missing_ablation | C | There is already K sensitivity up to K=4; asking beyond K=4 is plausible but too demanding for a verified main result. |
| YXn76HMetm | equalal_baseline | missing_baseline | B | Paper-named comparator issue; defensible as a same-setting missing baseline concern. |

## Summary Judgment

Manual A/B clusters: 8/9.

Paper-facing conservative count: 8 review-worthy clusters, with 3 strong A-class issues and 5 defensible B-class issues. The system count is 9 verified clusters, but the `number_motion_components_beyond` cluster should be excluded from any paper-ready precision claim unless further manually confirmed.

## Remaining Risks

- The live recovery table still contains stale absence repairs because the API run happened before the final TargetRefine2 guard. A fresh rerun with the final guard is needed before claiming live recovery counts.
- `reviewer_candidate_review_issue_critique_payload_count=2`; most verified clusters are still deterministic seeds, not free Critique discovery.
- Direct quote-grounded `review_negative_verified_count` remains 0 in this fresh run. The current contribution is obligation-grounded issue verification, not direct negative quote discovery.
