# P29 Manual Review Issue Cluster Audit

- source case table: `P29_DISCOVERY_EXPAND_MIMO_160531_TARGETGUARD3_REVIEW_ISSUE_CASE_TABLE.json`
- audit scope: P29 2026-07-01 verifier-passing issue clusters
- audit unit: deduplicated system cluster, not raw row

## Summary

- system rows: `20`
- system clusters: `15`
- manual duplicate merges: `1`
- manual deduplicated clusters: `14`
- strict A/B clusters: `8`
- permissive A/B clusters: `9`
- A/B/C/D/MERGE: `4` / `4` / `3` / `3` / `1`

Paper-facing interpretation: P29 produced 20 verifier-passing rows and 15 system clusters. Manual spot-checking supports 8 strict A/B clusters, 9 under a permissive reading, after merging one direct-quote duplicate. The remaining risky cases are mostly counterevidence misses, overbroad protocol targets, or weak same-setting baseline assumptions.

## Cluster Labels

| paper | issue_type | target | origin | label | permissive | merge target | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WNxlJJIEVj | missing_ablation | planning_module | deterministic_reviewer_seed | C |  |  | Planning Module is a real component, but the verified claim is about the contrastive mechanism and the paper already contains contrastive ablations; the target is weakly aligned. |
| 9zEBK3E9bX | missing_ablation | comparing_occupancy_prediction_alternative_pretext_tasks_masked_point | critique_payload_candidate | B |  |  | Occupancy prediction is a claimed pretraining objective and alternative pretext comparisons are review-worthy; Table 6 may partially cover this, so it is defensible rather than strong. |
| GE6iywJtsV | reproducibility_gap | implementation_reproducibility_details | deterministic_reviewer_seed | B |  |  | The GrCN method is central and the visible paper text lacks common reproducibility details such as learning rate, seed, epochs, or implementation configuration. |
| WpXq5n8yLb | missing_ablation | recurrent_draft_model | deterministic_reviewer_seed | A |  |  | The recurrent draft model is explicitly named as one of three performance-driving mechanisms; paper text shows other ablations but not an isolated RNN draft-model ablation. |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | deterministic_reviewer_seed | A |  |  | The acceptance prediction head is a named core mechanism for adaptive candidate length and no ablation evidence was found in the visible full text. |
| a6SntIisgg | missing_ablation | global_encoder | deterministic_reviewer_seed | A |  |  | The global encoder is part of the paper's named local-global contribution; the visible ablation section focuses on losses rather than isolating the global branch. |
| QAgwFiIY4p | reproducibility_gap | implementation_reproducibility_details | deterministic_reviewer_seed | B |  |  | The PSRD/PST method is central and the visible text gives little training configuration, seed, or hyperparameter detail; this is a valid reproducibility concern but somewhat generic. |
| TPAj63ax4Y | missing_baseline | lavt | claim_obligation_fallback | D |  |  | The full paper table already includes LAVT as a fully supervised reference; the issue confuses cross-setting comparison with a missing same-setting baseline. |
| mHv6wcBb0z | missing_ablation | generalized_noise_regularization | deterministic_reviewer_seed | A |  |  | Generalized noise regularization is the paper-named central mechanism for NR-DCCA, and no visible ablation of the mechanism was found. |
| YXn76HMetm | missing_baseline | equalal_baseline | deterministic_reviewer_seed | C | B |  | EqualAL is paper-named related work, but same-setting comparability to HALO's active domain adaptation setting is uncertain from the verified bundle. |
| YXn76HMetm | evaluation_protocol_risk | same-budget_same-hardware_fair-comparison_protocol_for_ripu | deterministic_reviewer_seed | D |  |  | The visible text provides ADA protocol, label budget, dataset, and training protocol details, so the same-budget/same-hardware target is overbroad and counterevidenced. |
| YXn76HMetm | missing_ablation | region-based_hyperbolic_feature_reweighting_hfr_mechanism_module | claim_obligation_fallback | D |  |  | The paper explicitly analyzes HFR and reports a +1.6 mIoU effect and robustness/stability benefit; this is a counterevidence miss. |
| KOUAayk5Kx | evaluation_protocol_risk | split_threshold_seed_same-budget_protocol_for_ogl-enhanced | deterministic_reviewer_seed | C |  |  | The fairness/protocol concern is plausible, but the target bundles split, threshold, seed, and budget too broadly while the paper gives several settings and comparison details. |
| XH3OiIhtvf | result_claim_mismatch | incorporating a secure aggregator in the federated model results in a less favor | direct_quote | MERGE |  | review-issue-cluster-xh3oiihtvf-quote-grounded-review-issue-negative-result-incorporating-a-secure-aggregator-in-the-federated-model-results- | This is the same secure-aggregator degradation quote and same claim area as the negative-result cluster; it should not count as a separate paper-facing issue. |
| XH3OiIhtvf | negative_result | incorporating a secure aggregator in the federated model results in a less favor | direct_quote | B |  |  | The copied quote is a real paper-negative result showing secure aggregation hurts performance; it is defensible but not a strong independent issue because the paper itself acknowledges part of it. |
