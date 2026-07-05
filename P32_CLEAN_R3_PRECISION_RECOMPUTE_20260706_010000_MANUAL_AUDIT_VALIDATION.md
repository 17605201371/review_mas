# P31.6 Manual Audit Validation

- run: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000`
- status: **PASS**

## Summary

| metric | value |
|---|---:|
| `critique_origin_clusters` | 6 |
| `manual_A_clusters` | 3 |
| `manual_B_clusters` | 4 |
| `manual_A_B_clusters` | 7 |
| `manual_C_clusters` | 2 |
| `manual_D_clusters` | 0 |
| `manual_MERGE_clusters` | 0 |
| `unfilled_clusters` | 0 |
| `critique_origin_manual_A_B_clusters` | 5 |
| `deterministic_seed_manual_A_B_clusters` | 2 |
| `critique_origin_D_clusters` | 0 |

## Cluster Labels

| label | paper | type | target | decision | reason |
|---|---|---|---|---|---|
| A | GE6iywJtsV | missing_ablation | graph_control_module | A | The paper presents Graph ControllNet as a central graph-control mechanism for constrained diffusion, and the audited evidence does not show a component-isola... |
| B | HPuLU6q7xq | missing_ablation | modeling_coarse_and_fine-grained_fusion | B | The coarse/fine personality modeling is a real component family and the paper reports ablation-style results, but the concern should be limited to whether th... |
| B | HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | B | GPT-4 is paper-named in the surrounding motivation for role-playing ability, while the experimental comparison appears to use LLaMA/DeepSeek/Orca-style basel... |
| A | NnExMNiTHw | missing_ablation | acceptance_prediction_head | A | The acceptance prediction head is central to adaptive candidate-length selection and latency reduction, while the visible evaluation does not isolate the hea... |
| C | QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | C | The target is over-specific for a partly theoretical bijection/symmetric-rank-decomposition claim. It may be a diagnosis question, but a component ablation i... |
| B | WpXq5n8yLb | missing_ablation | recurrent_draft_model | B | The recurrent draft model is a named mechanism and the paper contains ablations for related decoding settings, but no clean non-recurrent draft-model isolati... |
| B | YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | B | PixelPick and EqualAL are paper-named active-learning baselines; the visible results table excerpt is truncated and does not clearly establish same-setting c... |
| A | fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | A | The claim explicitly mentions computational efficiency, reduced runtime, or communication overhead, but the verified inventory is accuracy-oriented and does ... |
| C | ye3NrNrYOY | missing_ablation | fixed_module | C | The paper has an ablation section varying latent causal-variable count, so the machine target overstates the gap. It may remain a weak diagnosis about isolat... |
