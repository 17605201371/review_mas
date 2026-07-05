# P31.6 Manual Audit Validation

- run: `P32_CLEAN_R1_20260705_232527`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 6 |
| `manual_A_clusters` | 2 |
| `manual_B_clusters` | 5 |
| `manual_A_B_clusters` | 7 |
| `manual_C_clusters` | 3 |
| `manual_D_clusters` | 7 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 5 |
| `deterministic_seed_manual_A_B_clusters` | 1 |
| `critique_origin_D_clusters` | 1 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| C | 9zEBK3E9bX | missing_ablation | sz-softmax_loss | downgrade_to_diagnosis_pending | The loss-term concern is too narrow for a strong paper-facing issue because the paper already reports module-level ablations, while the exact Lovasz-Softmax ... |
| B | GE6iywJtsV | missing_ablation | graph_control_module | keep_with_careful_wording | The graph control module is central to the claimed constrained diffusion method, but the observed comparisons do not isolate its contribution. This is a defe... |
| D | GE6iywJtsV | insufficient_evaluation | et al., 2004) in our study, we utilized an unconditioned midi model as the basel | reject_false_positive | This cluster misread a positive baseline-comparison quote as a negative evaluation issue, so it should not be used as a review concern. |
| C | HPuLU6q7xq | missing_ablation | modeling_coarse_and_fine-grained_fusion | downgrade_to_diagnosis_pending | The target is vague and partly overlapped with existing PTIT/PSIT and ablation context. It is not strong enough as a paper-facing missing-ablation claim with... |
| B | HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | keep_with_careful_wording | The paper claims superior OrcaBench performance and discusses GPT-4 as a salient role-playing LLM, but the observed experiments do not include a same-setting... |
| B | NnExMNiTHw | missing_ablation | acceptance_prediction_head | keep_with_careful_wording | The acceptance prediction head is central to adaptive candidate-length selection. Existing comparisons show end-to-end gains but do not isolate the head/trai... |
| C | QAgwFiIY4p | efficiency_cost_gap | efficiency_resource_measurement | downgrade_to_diagnosis_pending | The parameter-measurement concern is plausible but too narrow as a strong review issue because the paper contains partial parameter-efficiency discussion. It... |
| D | QAgwFiIY4p | missing_robustness_or_generalization | held-out_coverage_for_parameter-efficient | reject_false_positive | This is a generic coverage seed that overstates a missing-evaluation issue despite broad multi-benchmark evaluation in the paper. |
| B | WpXq5n8yLb | missing_ablation | recurrent_draft_model | keep_with_careful_wording | The recurrent draft model is central, and existing baselines do not cleanly isolate recurrence while controlling the rest of ReDrafter. This is a defensible ... |
| A | XH3OiIhtvf | negative_result | incorporating a secure aggregator in the federated model results in a less favor | keep_as_clear_issue | The quote directly qualifies or contradicts the claim that secure aggregation preserves/improves the federated model outcome. This is a clear paper-grounded ... |
| D | XyB4VvF01X | missing_ablation | graph2tac_learns_hierarchical_representation_module | reject_false_positive | The audited text already contains the relevant no-definition-task variant, so the missing-ablation cluster is contradicted by paper text. |
| B | YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | keep_with_careful_wording | HALO claims SOTA active learning under domain shift and names PixelPick/EqualAL as relevant prior work, but the audited result context does not show same-set... |
| D | YXn76HMetm | missing_robustness_or_generalization | held-out_coverage_for_equalal | reject_false_positive | This seed turns a named related method into a generic held-out-coverage concern despite substantial benchmark coverage, so it is a false positive. |
| D | a6SntIisgg | missing_ablation | architecture_global_encoder | reject_false_positive | The missing-ablation claim is contradicted by an explicit model-architecture ablation table that includes Global Encoder variants. |
| D | a6SntIisgg | scope_overclaim | held-out_coverage_for_source-to-target | reject_false_positive | The scope-overclaim/held-out-coverage cluster is contradicted by the UDA benchmark design and multiple source-to-target evaluations. |
| A | fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | keep_as_clear_issue | The paper makes explicit efficiency claims without concrete resource-cost measurements in the audited evidence. This is a clear paper-facing support gap. |
| D | mHv6wcBb0z | missing_ablation | noise_perform_specific_regularization | reject_false_positive | The missing-ablation cluster is contradicted by DCCA/NR-DCCA comparisons and noise-regularization analyses already present in the paper. |
