# Model Transfer Funnel Audit v1

本审计用于区分“模型本身不强”和“框架把模型能力压平”。它不只看 final reward，而是看 raw payload → final support → recovery/flaw 的漏斗。

## Aggregate Metrics
| label | n | reward | evidence_support_score | payload_evidence_total | final_support_total | final_support_direct_model | final_support_fallback | fallback_final_support_rate | independent_final_support_groups | support_trace_dropped | evidence_question_only_turns | recovery_effective_repair |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| deepseek_full8 | 8 | 0.5060 | 0.3854 | 57.0000 | 24.0000 | 24.0000 | 0.0000 | 0.0000 | 19.0000 | 33.0000 | 10.0000 | 1.0000 |
| deepseek_batch2 | 8 | 0.4689 | 0.3224 | 52.0000 | 16.0000 | 16.0000 | 0.0000 | 0.0000 | 16.0000 | 30.0000 | 14.0000 | 2.0000 |

## Support Drop Reasons
### deepseek_full8
- `hygiene_filtered`: 17
- `semantic_mismatch`: 9
- `weak_support_depth`: 7

### deepseek_batch2
- `hygiene_filtered`: 21
- `semantic_mismatch`: 6
- `weak_support_depth`: 2
- `missing_verified_quote`: 1

## Interpretation
- `deepseek_batch2` 相对 `deepseek_full8` 的平均 reward 差值为 `-0.0371`，evidence_support 差值为 `-0.0630`。
- final support fallback rate 差值为 `0.0000`。如果更强模型的 direct_model_final_support 增加，说明模型能力没有完全被规则压平。
- 如果 raw payload 增加但 final support 没增加，优先检查 final-view guard / support-depth / semantic mismatch。
- 如果 raw payload 没增加，优先检查 context selection、quote bank、target selection 和模型适配 prompt。
