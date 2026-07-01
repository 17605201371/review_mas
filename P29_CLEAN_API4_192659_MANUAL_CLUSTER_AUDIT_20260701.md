# P29 Manual Review Issue Cluster Audit

- source case table: `P29_CLEAN_API4_192659_REVIEW_ISSUE_CASE_TABLE.json`
- audit scope: P29 2026-07-01 verifier-passing issue clusters
- audit unit: deduplicated system cluster, not raw row

## Summary

- system rows: `22`
- system clusters: `18`
- manual duplicate merges: `0`
- manual deduplicated clusters: `18`
- strict A/B clusters: `6`
- permissive A/B clusters: `8`
- A/B/C/D/MERGE: `3` / `3` / `3` / `9` / `0`

Paper-facing interpretation: the source run produced 22 verifier-passing rows and 18 system clusters. Manual spot-checking supports 6 strict A/B clusters, 8 under a permissive reading, after merging 0 duplicate cluster(s). The remaining risky cases are mostly counterevidence misses, overbroad protocol targets, weak same-setting baseline assumptions, or malformed/generic missing-ablation targets.

## Cluster Labels

| paper | issue_type | target | origin | label | permissive | merge target | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7Dub7UXTXN | reproducibility_gap | implementation_reproducibility_details | critique_payload_candidate | D |  |  | The verified bundle itself quotes that hyperparameters are in the supplementary implementation section; without auditing that supplement, this is a retrieval/supplement-coverage miss rather than a confirmed paper defect. |
| 9zEBK3E9bX | missing_ablation | unified_scene_representation | deterministic_reviewer_seed | B |  |  | The unified 3D representation is central to SPOT and a reviewer could ask for a cleaner isolation; Table 5/6 task-strategy results partially address it, so this is defensible rather than strong. |
| 9zEBK3E9bX | evaluation_protocol_risk | split_threshold_seed_same-budget_protocol_for_spot | deterministic_reviewer_seed | C |  |  | The protocol target bundles split, threshold, seed, and same-budget concerns too broadly; the paper has an experimental setup, but seed-level reproducibility may still be under-specified. |
| GE6iywJtsV | reproducibility_gap | implementation_reproducibility_details | deterministic_reviewer_seed | B |  |  | The GrCN/ControllNet architecture is central and the visible extracted paper text lacks common training configuration, seed, learning-rate, or implementation details. |
| WpXq5n8yLb | missing_ablation | recurrent_draft_model | deterministic_reviewer_seed | A |  |  | The recurrent draft model is a named performance-driving mechanism; the visible text supports the component anchor but does not show an isolated recurrent-draft-model ablation. |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | deterministic_reviewer_seed | A |  |  | The acceptance prediction head is a named core mechanism for adaptive candidate length, and no visible ablation evidence isolates its contribution. |
| a6SntIisgg | missing_ablation | ional_branch | deterministic_reviewer_seed | C | B |  | The intended LogoRA branch-level concern is plausible because the ablation table focuses on losses, but the extracted target is malformed ('ional branch') and should not be treated as a strong paper-facing defect. |
| cklg91aPGk | missing_robustness_or_generalization | held-out_coverage_for_gcl | deterministic_reviewer_seed | D |  |  | The full text reports additional heterophily, large-scale, and multiple node-classification benchmarks, so the held-out coverage issue is counterevidenced. |
| fGXyvmWpw6 | missing_ablation | the_total_loss | deterministic_reviewer_seed | D |  |  | The paper explicitly has an ablation section studying the choice of regularization loss, lambda weighting, distillation iterations, and data update steps, so the total-loss ablation target is counterevidenced. |
| fGXyvmWpw6 | missing_ablation | via_aggregation_local_network | deterministic_reviewer_seed | D |  |  | Aggregation of local network updates is a generic federated-learning mechanism, not a paper-specific contribution mechanism that should become a verified missing-ablation issue. |
| QAgwFiIY4p | reproducibility_gap | implementation_reproducibility_details | deterministic_reviewer_seed | B |  |  | The PST/PSRD method is central and the visible text gives limited training configuration or seed detail; this is a defensible reproducibility concern, though somewhat generic. |
| TPAj63ax4Y | missing_baseline | standard_ris_segmentation_baselines_and_datasets_used_the | deterministic_reviewer_seed | D |  |  | The main comparison table includes zero-shot, weakly supervised, and fully supervised RIS baselines including LAVT; the issue overgeneralizes a baseline concern. |
| mHv6wcBb0z | missing_ablation | generalized_noise_regularization | deterministic_reviewer_seed | A |  |  | Generalized noise regularization is the paper-named central mechanism for NR-DCCA, and no visible evidence isolates its contribution. |
| xUe1YqEgd6 | missing_ablation | only_comprises_one_head | deterministic_reviewer_seed | D |  |  | The target is an ordinary architecture description rather than a named contribution mechanism, and the paper already contains a component ablation section. |
| xUe1YqEgd6 | missing_ablation | the_quadratic_motion_model_for_the_multi-segment | critique_payload_candidate | D |  |  | Section 5.1 explicitly ablates the space-time quadratic motion model against an alternative, so this is a counterevidence miss. |
| YXn76HMetm | missing_baseline | equalal_baseline | deterministic_reviewer_seed | C | B |  | EqualAL is a paper-named related method, but same-setting comparability to HALO's active domain-adaptation setup is uncertain from the verified bundle. |
| YXn76HMetm | evaluation_protocol_risk | same-budget_same-hardware_fair-comparison_protocol_for_ripu | deterministic_reviewer_seed | D |  |  | The paper provides ADA protocol, datasets, label-budget framing, and training-protocol details; the same-budget/same-hardware target is overbroad. |
| YXn76HMetm | missing_ablation | carefully_initialize_the_hyperbolic_network | deterministic_reviewer_seed | D |  |  | The verified inventory points to the main ablation and HFR/initialization analysis, so the target is not a clean missing-ablation issue. |
