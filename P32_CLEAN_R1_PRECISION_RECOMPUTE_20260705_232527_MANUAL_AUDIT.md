# P32 Clean R1 Precision Recompute Manual Audit

- run: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527`
- source case table: `P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527_REVIEW_ISSUE_CASE_TABLE.json`
- result: strict manual validation PASS (A=2, B=5, C=4, D=0)

| label | paper | origin | type | target | reason |
|---|---|---|---|---|---|
| `C` | `9zEBK3E9bX` | `deterministic_seed` | `missing_ablation` | `sz-softmax_loss` | The loss-term concern is too narrow for a strong paper-facing issue because the paper already reports module-level ablations, while the exact Lovasz-Softmax isolation is not cle... |
| `B` | `GE6iywJtsV` | `critique_payload` | `missing_ablation` | `graph_control_module` | The graph control module is central to the claimed constrained diffusion method, but the observed comparisons do not isolate its contribution. This is a defensible ablation conc... |
| `C` | `HPuLU6q7xq` | `deterministic_seed` | `missing_ablation` | `modeling_coarse_and_fine-grained_fusion` | The target is vague and partly overlapped with existing PTIT/PSIT and ablation context. It is not strong enough as a paper-facing missing-ablation claim without a tighter compon... |
| `B` | `HPuLU6q7xq` | `critique_payload` | `missing_baseline` | `paper-named_gpt-4_baseline` | The paper claims superior OrcaBench performance and discusses GPT-4 as a salient role-playing LLM, but the observed experiments do not include a same-setting GPT-4 comparison. T... |
| `B` | `NnExMNiTHw` | `critique_payload` | `missing_ablation` | `acceptance_prediction_head` | The acceptance prediction head is central to adaptive candidate-length selection. Existing comparisons show end-to-end gains but do not isolate the head/training choices, so thi... |
| `C` | `QAgwFiIY4p` | `claim_obligation` | `efficiency_cost_gap` | `efficiency_resource_measurement` | The parameter-measurement concern is plausible but too narrow as a strong review issue because the paper contains partial parameter-efficiency discussion. It should remain diagn... |
| `B` | `WpXq5n8yLb` | `deterministic_seed` | `missing_ablation` | `recurrent_draft_model` | The recurrent draft model is central, and existing baselines do not cleanly isolate recurrence while controlling the rest of ReDrafter. This is a defensible ablation concern wit... |
| `A` | `XH3OiIhtvf` | `quote_grounded` | `negative_result` | `incorporating a secure aggregator in the federated model results in a less favor` | The quote directly qualifies or contradicts the claim that secure aggregation preserves/improves the federated model outcome. This is a clear paper-grounded negative result. |
| `B` | `YXn76HMetm` | `critique_payload` | `missing_baseline` | `paper-named_pixelpick_baseline` | HALO claims SOTA active learning under domain shift and names PixelPick/EqualAL as relevant prior work, but the audited result context does not show same-setting comparisons to ... |
| `C` | `a6SntIisgg` | `deterministic_seed` | `missing_ablation` | `feature_dependencies_self-attention_mechanism` | This is an over-specific self-attention/component-isolation target. The paper reports model-architecture and fusion-method ablations around the global/local representation desig... |
| `A` | `fGXyvmWpw6` | `critique_payload` | `efficiency_cost_gap` | `efficiency_resource_measurement` | The paper makes explicit efficiency claims without concrete resource-cost measurements in the audited evidence. This is a clear paper-facing support gap. |
