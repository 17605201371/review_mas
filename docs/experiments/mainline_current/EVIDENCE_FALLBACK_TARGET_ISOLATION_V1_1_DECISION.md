# Evidence Fallback Target Isolation v1.1 Decision

## 结论

**保留 v1.1，作为 v1 的修正版。**

v1 的方向是对的：Evidence Agent 不应该把 `claim-fallback-*` 当作可验证目标暴露给模型。但 fulltest39 诊断显示，单纯剔除 fallback target 会在部分 turn 中让 Evidence Agent 没有可用真实 target，导致 evidence 形成路径被压缩。v1.1 修正了这个问题：当 manager 给出的 target 只有 fallback claim，而当前 `ReviewState` 里存在真实 claim 时，Evidence observation 会剔除 fallback claim，并用真实 claim 候选替代，而不是把 target slice 留空。

这仍然是 Evidence 输入卫生补丁，不改变 final decision、recovery、fallback 生成、state merge 或 validator。

## mixed16 标准分析

输入：`outputs/results_main/review_infer/evidence_fallback_target_isolation_v1_1_mixed16.jsonl`

| 指标 | v1.1 结果 |
|---|---:|
| rows | 16 |
| evidence_calls | 92 |
| evidence_valid_payload_rate | 0.8370 |
| evidence_fallback_payload_count | 2 |
| evidence_parse_error_count | 0 |
| raw_positive_evidence_mentions | 52 |
| raw_insufficient_excerpt_mentions | 0 |
| final_strong_support_total | 8 |
| strong_support_on_real_claim | 8 |
| strong_support_on_fallback_claim | 0 |
| unbound_strong_support | 0 |
| fallback_extraction_strong_support | 0 |
| evidence_binding_error_count | 0 |
| strong_support_binding_precision | 1.0000 |
| rows_with_2plus_real_strong_support | 0 |
| accept_samples_with_2plus_real_strong_support | 0 |

## 对比结论

| 指标 | JSON robustness v1.1 | isolation v1 | isolation v1.1 |
|---|---:|---:|---:|
| evidence_turn_fb_raw_targets | 8 | 9 | 4 |
| fallback_targets_omitted_turns | 0 | 0 | 4 |
| fallback_targets_replaced_turns | 0 | 0 | 4 |
| payload fallback-bound evidence | 6 | 3 | 2 |
| payload fallback-bound strong | 2 | 0 | 0 |
| state fallback-bound evidence | 5 | 1 | 1 |
| source=fallback-extraction state evidence | 7 | 7 | 2 |
| real strong support | 5 | 5 | 8 |
| final strong support | 5 | 5 | 8 |
| final accept | 0 | 0 | 0 |

v1.1 的关键收益不是让 final decision 立刻出现 accept，而是更干净地维持 Evidence 输入边界：fallback target 不再暴露给模型，同时 fallback-only target 不会导致 Evidence Agent 没有真实 claim 可看。结果上，fallback source evidence 明显下降，real strong support 从 5 提升到 8，fallback strong support 继续保持 0。

## 为什么保留

1. **比 v1 更稳**：v1 只剔除 fallback target，v1.1 在剔除后补入真实 claim 候选，避免空 target 副作用。
2. **污染继续下降**：payload fallback-bound evidence 从 6 降到 2，state source fallback evidence 从 7 降到 2。
3. **正向证据不再被压缩**：real strong support 从 v1 的 5 提升到 8。
4. **安全边界未破坏**：fallback strong support、unbound strong support 和 binding error 仍为 0。

## 不能过度解读

v1.1 仍没有解决 accept collapse：`rows_with_2plus_real_strong_support` 仍为 0，所有 mixed16 样本最终仍为 reject。说明当前瓶颈不是 fallback target isolation，而是更深一层的 non-abstract / empirical / independent support formation，以及 final-view hygiene / criterion grounding 如何使用这些证据。

## 下一步

保留 v1.1 后，下一步不应回到 sticky、throttle、support-pass 或 final decision 阈值硬调。更合理的下一步是：

1. 用 v1.1 作为 Evidence 输入卫生基线；
2. 如需更大验证，再跑 fulltest39，重点看 real/non-abstract support 是否不下降、fallback source evidence 是否继续下降；
3. 继续分析为什么大多数样本只能形成 0 或 1 条 real strong support，而不是 2+ independent support；
4. criterion/report 方向继续保持 offline/report-only，不接入 accept/reject。

## fulltest39 补充结论

v1.1 fulltest39 已完成。标准分析显示：`evidence_fallback_payload_count=13`，`strong_support_on_real_claim=9`，`strong_support_on_fallback_claim=0`，`fallback_extraction_strong_support=0`，`binding_precision=1.0`，`rows_with_2plus_real_strong_support=0`，最终仍为 39/39 reject。自定义审计显示，相比 isolation v1，state source=fallback-extraction evidence 从 21 降到 13，payload fallback-bound evidence 从 21 降到 14，real strong support 从 7 回升到 9。

结论不变：保留 v1.1 作为 Evidence 输入卫生基线，但它不是 accept collapse 的完整解决方案。下一步应分析为什么 fulltest39 中 real strong support 多为 0 或 1，重点查 evidence raw output、state merge/retention、non-abstract/empirical/independent support 形成链路。

