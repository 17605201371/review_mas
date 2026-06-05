# Evidence Fallback Target Isolation v1 Decision

## 结论

**保留。**

本轮不是为了提升 accept/reject，也不是为了增加 strong support 数量，而是修掉 Evidence Agent 输入层的一个污染入口：当 manager target 是 `claim-fallback-*` 时，Evidence Agent 过去仍会在 `target_claims` 中看到 fallback claim，从而围绕 fallback target 生成 evidence。Evidence Binding v1 会在 state merge 层把这些证据降权，但这仍然会浪费 evidence turn，并增加 fallback evidence / unresolved / critique 噪声。

v1 的最小修复是：Evidence Agent 的 `target_claims` 和 `allowed_claim_ids` 只暴露真实 claim；fallback claim target 被剔除并记录为 `fallback_claim_targets_omitted`。

## mixed16 验证结果

输入：`outputs/results_main/review_infer/evidence_fallback_target_isolation_v1_mixed16.jsonl`

按标准分析脚本口径：

| 指标 | 结果 |
|---|---:|
| rows | 16 |
| evidence_calls | 87 |
| evidence_valid_payload_rate | 0.8276 |
| evidence_fallback_payload_count | 7 |
| evidence_parse_error_count | 0 |
| raw_positive_evidence_mentions | 38 |
| raw_insufficient_excerpt_mentions | 2 |
| final_strong_support_total | 5 |
| strong_support_on_real_claim | 5 |
| strong_support_on_fallback_claim | 0 |
| unbound_strong_support | 0 |
| fallback_extraction_strong_support | 0 |
| strong_support_binding_precision | 1.0000 |
| rows_with_2plus_real_strong_support | 0 |

补充审计显示，与 `evidence_json_robustness_v1_1_mixed16` 相比：

| 指标 | v1.1 | isolation v1 | 判断 |
|---|---:|---:|---|
| state fallback-bound evidence | 5 | 1 | 明显下降 |
| payload fallback-bound evidence | 6 | 3 | 下降 |
| payload model fallback strong | 2 | 0 | 下降到 0 |
| real strong support | 5 | 5 | 持平 |
| final strong support | 5 | 5 | 持平 |
| fallback strong support | 0 | 0 | 维持安全 |

按更宽松的 custom fallback 口径，fallback payload 可能从 8 升到 10；这说明剔除 fallback target 后，部分 Evidence turn 会更保守地走 fallback/unresolved。但这些 fallback 不再污染 strong support，也没有破坏 real strong support。

## 为什么保留

保留理由有三点：

1. **污染下降**：fallback-bound evidence 在 state 与 payload 两层都下降，model fallback strong 降到 0。
2. **主安全指标未坏**：real strong support 持平，fallback strong support 维持 0，binding precision 维持 1.0。
3. **行为边界清楚**：本改动只改变 Evidence observation 的目标暴露，不改 final decision、不改 recovery、不改 state merge、不改 fallback 生成逻辑。

这意味着它是一个低风险的输入卫生补丁，而不是新的 controller。

## 不能过度解读

本轮没有解决 positive support formation 不足：

- `rows_with_2plus_real_strong_support` 仍为 0；
- accept 样本没有形成足够多的 real-claim strong support；
- non-abstract / empirical / independent support 仍是下一阶段瓶颈。

因此它不能作为“性能提升实验”写成主贡献，只能作为 Evidence Binding / JSON Robustness 主线下的污染隔离补丁。

## 日志口径修正

本轮之后补齐了 `fallback_claim_targets_omitted` 的 turn log 落盘：

- `render_evidence_observation(...)` 会把 omitted fallback targets 写回当前 turn 的 `manager_payload`；
- `build_turn_log(...)` 会记录 `fallback_claim_targets_omitted` 与 `fallback_claim_targets_omitted_count`；
- 单测覆盖 observation 与 turn log 两层。

注意：当前 mixed16 结果是在日志口径补齐前跑出的，因此该 jsonl 不能直接统计 omitted count；下一次运行会包含该字段。

## 下一步

下一步不应回到 sticky / throttle / support-pass / final-decision threshold。更合理的下一刀是继续沿 Evidence 质量主线推进：

1. 固定当前 Evidence Binding + JSON Robustness + fallback target isolation 作为 4B 主线候选；
2. 在 fulltest39 上确认 fallback-bound evidence 是否继续下降、real strong support 是否不下降；
3. 继续分析为什么 non-abstract / empirical / independent support 形成不足；
4. 如要继续改 runtime，优先考虑 Evidence observation 中的 real claim selection / section evidence alignment，而不是 controller。

## v1.1 补充结论

v1 之后又做了一个更稳的 v1.1：当 manager target 只有 `claim-fallback-*`，但 state 中存在真实 claim 时，Evidence observation 不再只剔除 fallback target 后留下空 target，而是用真实 claim 候选替代。mixed16 结果显示：

- `evidence_fallback_payload_count` 降到 2；
- `state source=fallback-extraction evidence` 从 7 降到 2；
- `payload fallback-bound evidence` 从 6 降到 2；
- `real strong support` 从 5 提升到 8；
- `fallback strong support` 继续为 0；
- `rows_with_2plus_real_strong_support` 仍为 0。

因此最终应保留 v1.1，而不是只保留 v1。v1.1 的定位仍是 Evidence 输入卫生补丁，不是 final decision 或 support formation 的完整解决方案。

