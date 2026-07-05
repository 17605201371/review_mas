# P32 Manual Audit: P32_CLEAN_R1_20260705_232527

- audit date: `2026-07-05`
- source case table: `P32_CLEAN_R1_20260705_232527_REVIEW_ISSUE_CASE_TABLE.json`
- status: **FILLED_PENDING_VALIDATION**
- strict expectation: D clusters make manual gate fail; allow-D diagnostic should be used only to read Critique A/B recurrence.

| label | paper | origin | type | target | decision | rationale |
|---|---|---|---|---|---|---|
| C | 9zEBK3E9bX | deterministic_seed | missing_ablation | sz-softmax_loss | downgrade_to_diagnosis_pending | The loss-term concern is too narrow for a strong paper-facing issue because the paper already reports module-level ablations, while the exact Lovasz-Softmax isolation is not cle... |
| B | GE6iywJtsV | critique_payload | missing_ablation | graph_control_module | keep_with_careful_wording | The graph control module is central to the claimed constrained diffusion method, but the observed comparisons do not isolate its contribution. This is a defensible ablation conc... |
| D | GE6iywJtsV | quote_grounded | insufficient_evaluation | et al., 2004) in our study, we utilized an unconditioned midi model as the basel | reject_false_positive | This cluster misread a positive baseline-comparison quote as a negative evaluation issue, so it should not be used as a review concern. |
| C | HPuLU6q7xq | deterministic_seed | missing_ablation | modeling_coarse_and_fine-grained_fusion | downgrade_to_diagnosis_pending | The target is vague and partly overlapped with existing PTIT/PSIT and ablation context. It is not strong enough as a paper-facing missing-ablation claim without a tighter compon... |
| B | HPuLU6q7xq | critique_payload | missing_baseline | paper-named_gpt-4_baseline | keep_with_careful_wording | The paper claims superior OrcaBench performance and discusses GPT-4 as a salient role-playing LLM, but the observed experiments do not include a same-setting GPT-4 comparison. T... |
| B | NnExMNiTHw | critique_payload | missing_ablation | acceptance_prediction_head | keep_with_careful_wording | The acceptance prediction head is central to adaptive candidate-length selection. Existing comparisons show end-to-end gains but do not isolate the head/training choices, so thi... |
| C | QAgwFiIY4p | claim_obligation | efficiency_cost_gap | efficiency_resource_measurement | downgrade_to_diagnosis_pending | The parameter-measurement concern is plausible but too narrow as a strong review issue because the paper contains partial parameter-efficiency discussion. It should remain diagn... |
| D | QAgwFiIY4p | deterministic_seed | missing_robustness_or_generalization | held-out_coverage_for_parameter-efficient | reject_false_positive | This is a generic coverage seed that overstates a missing-evaluation issue despite broad multi-benchmark evaluation in the paper. |
| B | WpXq5n8yLb | deterministic_seed | missing_ablation | recurrent_draft_model | keep_with_careful_wording | The recurrent draft model is central, and existing baselines do not cleanly isolate recurrence while controlling the rest of ReDrafter. This is a defensible ablation concern wit... |
| A | XH3OiIhtvf | quote_grounded | negative_result | incorporating a secure aggregator in the federated model results in a less favor | keep_as_clear_issue | The quote directly qualifies or contradicts the claim that secure aggregation preserves/improves the federated model outcome. This is a clear paper-grounded negative result. |
| D | XyB4VvF01X | claim_obligation | missing_ablation | graph2tac_learns_hierarchical_representation_module | reject_false_positive | The audited text already contains the relevant no-definition-task variant, so the missing-ablation cluster is contradicted by paper text. |
| B | YXn76HMetm | critique_payload | missing_baseline | paper-named_pixelpick_baseline | keep_with_careful_wording | HALO claims SOTA active learning under domain shift and names PixelPick/EqualAL as relevant prior work, but the audited result context does not show same-setting comparisons to ... |
| D | YXn76HMetm | deterministic_seed | missing_robustness_or_generalization | held-out_coverage_for_equalal | reject_false_positive | This seed turns a named related method into a generic held-out-coverage concern despite substantial benchmark coverage, so it is a false positive. |
| D | a6SntIisgg | deterministic_seed | missing_ablation | architecture_global_encoder | reject_false_positive | The missing-ablation claim is contradicted by an explicit model-architecture ablation table that includes Global Encoder variants. |
| D | a6SntIisgg | critique_payload | scope_overclaim | held-out_coverage_for_source-to-target | reject_false_positive | The scope-overclaim/held-out-coverage cluster is contradicted by the UDA benchmark design and multiple source-to-target evaluations. |
| A | fGXyvmWpw6 | critique_payload | efficiency_cost_gap | efficiency_resource_measurement | keep_as_clear_issue | The paper makes explicit efficiency claims without concrete resource-cost measurements in the audited evidence. This is a clear paper-facing support gap. |
| D | mHv6wcBb0z | deterministic_seed | missing_ablation | noise_perform_specific_regularization | reject_false_positive | The missing-ablation cluster is contradicted by DCCA/NR-DCCA comparisons and noise-regularization analyses already present in the paper. |

## Summary

- `system_clusters`: `17`
- `critique_origin_clusters`: `6`
- `manual_A_clusters`: `2`
- `manual_B_clusters`: `5`
- `manual_A_B_clusters`: `7`
- `manual_C_clusters`: `3`
- `manual_D_clusters`: `7`
- `manual_MERGE_clusters`: `0`
- `unfilled_clusters`: `0`
- `manual_A_B_clusters_by_origin`: `{'critique_payload': 5, 'deterministic_seed': 1, 'quote_grounded': 1}`
- `manual_D_clusters_by_origin`: `{'claim_obligation': 1, 'critique_payload': 1, 'deterministic_seed': 4, 'quote_grounded': 1}`
- `critique_origin_manual_A_B_clusters`: `5`
- `critique_origin_D_clusters`: `1`
- `status`: `FILLED_PENDING_VALIDATION`

## Notes

### 9zEBK3E9bX / sz-softmax_loss

- label: `C`
- raw check: checked: SPOT uses class-balancing cross entropy plus Lovasz-Softmax and includes a module-level ablation section with Table 6 over pre-training strategies.
- counterevidence check: checked: Table 6 covers occupancy/pre-training strategies, including loss balancing, but does not cleanly isolate Lovasz-Softmax itself; the existing ablation section weakens a broad missing-ablation claim.
- wording caution: If retained, phrase only as a possible loss-term isolation gap; do not claim the paper lacks ablations.
- downgrade reason: `over_specific_target_with_existing_ablation_section`

### GE6iywJtsV / graph_control_module

- label: `B`
- raw check: checked: Diff-Shape describes GrCN and a graph control module as central architecture components for shape-conditioned generation.
- counterevidence check: checked: no direct component-isolation ablation for the graph control module was found in the audited method/baseline windows; MIDI/SQUID/ShapeMol comparisons are end-to-end baselines.
- wording caution: Acknowledge the existing MIDI/SQUID/ShapeMol comparisons; limit the issue to component isolation of GrCN/graph control.

### GE6iywJtsV / et al., 2004) in our study, we utilized an unconditioned midi model as the basel

- label: `D`
- raw check: checked: the quote says the authors used unconditioned MIDI as a baseline and compared Diff-Shape with SQUID and ShapeMol.
- counterevidence check: checked: the same quote is evidence of an evaluation/baseline comparison rather than an insufficient-evaluation gap.
- false positive categories: `positive_baseline_comparison_misread_as_negative, quote_supports_evaluation_not_gap`

### HPuLU6q7xq / modeling_coarse_and_fine-grained_fusion

- label: `C`
- raw check: checked: Orca describes coarse-grained and fine-grained personality conditioning, PTIT/PSIT training modes, and says it conducts ablation studies.
- counterevidence check: checked: the audited windows show PTIT/PSIT/baseline context but do not give a clean missing-vs-present judgment for a specific coarse/fine fusion component.
- wording caution: Use only as a prompt for deeper manual review of coarse/fine modeling, not as a final review issue.
- downgrade reason: `vague_component_boundary_and_partial_existing_ablation_context`

### HPuLU6q7xq / paper-named_gpt-4_baseline

- label: `B`
- raw check: checked: GPT-4 appears as a motivating closed model in the paper text; the baseline window lists LLaMA3.1, DeepSeek, PCIP, and OrcaData/PTIT/PSIT variants.
- counterevidence check: checked: no same-setting GPT-4 OrcaBench comparison was found in the audited baseline/result windows.
- wording caution: Frame as absence of a strong closed-model reference point, not proof that GPT-4 was required or feasible.

### NnExMNiTHw / acceptance_prediction_head

- label: `B`
- raw check: checked: SpecDec++ describes a trained acceptance prediction head, weighted BCE training, stopping threshold, and fixed-K speculative decoding comparisons.
- counterevidence check: checked: fixed-K comparisons and implementation details do not isolate the learned head or its training/calibration choices from the rest of the adaptive policy.
- wording caution: Phrase as missing isolation of the learned head/calibration choices, not as absence of all baseline comparisons.

### QAgwFiIY4p / efficiency_resource_measurement

- label: `C`
- raw check: checked: PST claims fewer or comparable parameters and includes complexity/parameter-related discussion alongside graph-property and long-range benchmark results.
- counterevidence check: checked: the audited graph-property table window lacks parameter columns, but the broader paper text includes at least partial parameter/comparability support.
- wording caution: If used, ask for clearer parameter reporting per benchmark rather than claiming no parameter evidence exists.
- downgrade reason: `partial_parameter_support_present`

### QAgwFiIY4p / held-out_coverage_for_parameter-efficient

- label: `D`
- raw check: checked: PST is evaluated across synthetic substructure tasks, graph-property datasets, and long-range graph benchmarks.
- counterevidence check: checked: the broad held-out/coverage target is contradicted by the paper already covering multiple task families; it is not a specific missing robustness claim.
- false positive categories: `coverage_present, generic_heldout_target`

### WpXq5n8yLb / recurrent_draft_model

- label: `B`
- raw check: checked: ReDrafter identifies the RNN draft model as one of three key performance drivers and compares end-to-end against Medusa, EAGLE, and autoregressive baselines.
- counterevidence check: checked: the audited ablations cover beam width/batch size, dynamic tree attention, and distillation, but not a direct RNN-vs-non-RNN controlled ablation.
- wording caution: Acknowledge Medusa/EAGLE/end-to-end comparisons and narrow the issue to controlled recurrence isolation.

### XH3OiIhtvf / incorporating a secure aggregator in the federated model results in a less favor

- label: `A`
- raw check: checked: the paper text explicitly states that incorporating a secure aggregator gives a less favorable outcome than the baseline system.
- counterevidence check: checked: nearby EER discussion indicates lower EER is better; this is direct quote-grounded negative evidence for the secure-aggregator setting.
- wording caution: Mention the lower-is-better EER convention and the specific secure-aggregator setting.

### XyB4VvF01X / graph2tac_learns_hierarchical_representation_module

- label: `D`
- raw check: checked: Graph2Tac describes a definition task for hierarchical representations and reports G2T-NoDef, trained without a definition task.
- counterevidence check: checked: G2T-NoDef is direct counterevidence against a missing-ablation claim for the definition/hierarchical-representation component.
- false positive categories: `existing_ablation_counterevidence, missing_ablation_contradicted`

### YXn76HMetm / paper-named_pixelpick_baseline

- label: `B`
- raw check: checked: PixelPick and EqualAL appear in related/active-learning context; the result discussion emphasizes recent ADA methods such as RIPU/D2ADA and supervised DA baselines.
- counterevidence check: checked: no same-setting PixelPick/EqualAL result row was found in the audited result-table window, though HALO has substantial SOTA comparisons.
- wording caution: Frame as missing named AL baseline comparisons under comparable settings, not as absence of all SOTA/ADA baselines.

### YXn76HMetm / held-out_coverage_for_equalal

- label: `D`
- raw check: checked: HALO evaluates GTAV-to-Cityscapes, SYNTHIA-to-Cityscapes, Cityscapes-to-ACDC, and both convolutional and attention-based backbones.
- counterevidence check: checked: the broad held-out/coverage complaint is contradicted by the paper already reporting multiple domain-shift benchmarks and backbones.
- false positive categories: `coverage_present, generic_heldout_target`

### a6SntIisgg / architecture_global_encoder

- label: `D`
- raw check: checked: LogoRA includes an ablation table for model architecture with TCN, Transformer, PatchTST, Transformer+TCN, Global Encoder+TCN, Global Encoder+Local Encoder, and full LogoRA.
- counterevidence check: checked: this architecture table directly addresses the claimed missing global-encoder/component ablation boundary.
- false positive categories: `existing_ablation_counterevidence, missing_ablation_contradicted`

### a6SntIisgg / held-out_coverage_for_source-to-target

- label: `D`
- raw check: checked: LogoRA reports four time-series datasets and source-to-target UDA scenarios, with tables over multiple source/target pairs.
- counterevidence check: checked: the audited evidence already covers source-to-target transfer rather than merely single-domain performance.
- false positive categories: `coverage_present, scope_overclaim_contradicted_by_benchmark_design`

### fGXyvmWpw6 / efficiency_resource_measurement

- label: `A`
- raw check: checked: FedLGD repeatedly claims efficiency/scalability benefits from smaller virtual data and local-global distillation.
- counterevidence check: checked: audited windows show method/accuracy evidence and qualitative efficiency claims but no concrete runtime, memory, FLOP, hardware, or communication-cost measurement.
- wording caution: Tie the issue to empirical support for efficiency/resource-cost claims, not to the accuracy contribution.

### mHv6wcBb0z / noise_perform_specific_regularization

- label: `D`
- raw check: checked: NR-DCCA is compared against DCCA-based baselines, and the paper analyzes DCCA versus NR-DCCA behavior across training, synthetic data, and real-world datasets.
- counterevidence check: checked: those comparisons and analyses directly isolate the noise-regularization contribution enough to defeat a broad missing-ablation claim.
- false positive categories: `existing_baseline_counterevidence, missing_ablation_contradicted`
