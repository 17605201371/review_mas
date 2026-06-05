# Model Transfer Funnel Audit v1

本审计用于区分“模型本身不强”和“框架把模型能力压平”。它不只看 final reward，而是看 raw payload → final support → recovery/flaw 的漏斗。

## Aggregate Metrics
| label | n | reward | evidence_support_score | payload_evidence_total | final_support_total | final_support_direct_model | final_support_fallback | fallback_final_support_rate | independent_final_support_groups | support_trace_dropped | evidence_question_only_turns | recovery_effective_repair |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen8 | 8 | 0.4573 | 0.2687 | 19.0000 | 13.0000 | 2.0000 | 11.0000 | 0.8462 | 13.0000 | 4.0000 | 15.0000 | 1.0000 |
| deepseek_full8 | 8 | 0.5060 | 0.3854 | 57.0000 | 24.0000 | 24.0000 | 0.0000 | 0.0000 | 19.0000 | 33.0000 | 10.0000 | 1.0000 |

## Support Drop Reasons
### qwen8
- `claim_not_paper_extracted`: 2
- `semantic_mismatch`: 2

### deepseek_full8
- `hygiene_filtered`: 17
- `semantic_mismatch`: 9
- `weak_support_depth`: 7

## Paired Comparison
| paper_id | left | right | reward_delta | evidence_support_delta | final_support_delta | fallback_delta | payload_evidence_delta |
|---|---|---:|---:|---:|---:|---:|---:|
| 9zEBK3E9bX | qwen8 | deepseek_full8 | -0.0006 | 0.0000 | 6 | -2 | 8 |
| QAAsnSRwgu | qwen8 | deepseek_full8 | -0.0356 | -0.1167 | -2 | -2 | 6 |
| WLgbjzKJkk | qwen8 | deepseek_full8 | 0.0530 | 0.3500 | 2 | 0 | 4 |
| WNxlJJIEVj | qwen8 | deepseek_full8 | 0.0527 | 0.1417 | 1 | -3 | 4 |
| X41c4uB4k0 | qwen8 | deepseek_full8 | 0.2074 | 0.3875 | 2 | 0 | 3 |
| ZHr0JajZfH | qwen8 | deepseek_full8 | 0.0569 | 0.1833 | 2 | -2 | 5 |
| hj323oR3rw | qwen8 | deepseek_full8 | -0.0483 | -0.1750 | -1 | -2 | 2 |
| kam84eEmub | qwen8 | deepseek_full8 | 0.1039 | 0.1625 | 1 | 0 | 6 |

## Interpretation
- `deepseek_full8` 相对 `qwen8` 的平均 reward 差值为 `0.0487`，evidence_support 差值为 `0.1167`。
- final support fallback rate 差值为 `-0.8462`。如果更强模型的 direct_model_final_support 增加，说明模型能力没有完全被规则压平。
- 如果 raw payload 增加但 final support 没增加，优先检查 final-view guard / support-depth / semantic mismatch。
- 如果 raw payload 没增加，优先检查 context selection、quote bank、target selection 和模型适配 prompt。
