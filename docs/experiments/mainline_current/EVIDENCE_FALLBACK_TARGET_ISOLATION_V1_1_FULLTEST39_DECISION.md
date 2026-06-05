# Evidence Fallback Target Isolation v1.1 Fulltest39 Decision

## 结论

**fulltest39 支持保留 v1.1。**

本轮验证的是 Evidence 输入卫生，不是 final decision 改进。v1.1 在 fulltest39 上继续降低 fallback target / fallback evidence 污染，同时没有引入 fallback strong support 或 unbound strong support。它仍没有解决 all-reject 和 2+ real strong support 不足，因此不能被写成性能提升主结果。

## 标准分析结果

输入：`outputs/results_main/review_infer/evidence_fallback_target_isolation_v1_1_fulltest39.jsonl`

| 指标 | 结果 |
|---|---:|
| rows | 39 |
| evidence_calls | 216 |
| evidence_valid_payload_rate | 0.8287 |
| evidence_fallback_payload_count | 13 |
| evidence_parse_error_count | 0 |
| raw_positive_evidence_mentions | 101 |
| raw_insufficient_excerpt_mentions | 1 |
| final_strong_support_total | 9 |
| strong_support_on_real_claim | 9 |
| strong_support_on_fallback_claim | 0 |
| fallback_extraction_strong_support | 0 |
| evidence_binding_error_count | 0 |
| strong_support_binding_precision | 1.0000 |
| rows_with_2plus_real_strong_support | 0 |
| accept_samples_with_2plus_real_strong_support | 0 |
| final_accept | 0 |
| final_reject | 39 |

## 自定义 fallback 审计

| 指标 | integrated fulltest | isolation v1 | isolation v1.1 |
|---|---:|---:|---:|
| evidence_turn_fb_raw_targets | 18 | 40 | 32 |
| fallback_targets_omitted_turns | 0 | 40 | 32 |
| fallback_targets_replaced_turns | 0 | 0 | 32 |
| payload fallback-bound evidence | 26 | 21 | 14 |
| payload fallback-bound strong | 7 | 5 | 2 |
| state fallback-bound evidence | 18 | 15 | 12 |
| state source=fallback-extraction evidence | 17 | 21 | 13 |
| real strong support | 10 | 7 | 9 |
| final accept | 0 | 0 | 0 |

## 判断

v1.1 相比 v1 更合理：它不是简单剔除 fallback target，而是在 fallback-only target 场景下替换为真实 claim 候选。因此 fulltest39 上：

- `state source=fallback-extraction evidence` 从 21 降到 13；
- `payload fallback-bound evidence` 从 21 降到 14；
- `state fallback-bound evidence` 从 15 降到 12；
- `real strong support` 从 7 回升到 9；
- `strong_support_on_fallback_claim` 仍为 0。

这说明 v1.1 修复了 v1 的空 target 副作用，并继续降低 fallback 污染。

## 限制

fulltest39 仍然全 reject，且 `rows_with_2plus_real_strong_support = 0`。这说明主瓶颈已经不是 fallback target isolation，而是 Evidence Agent 仍难以形成多条独立、非摘要、实验/结果支撑的 real-claim strong support。

## 下一步

保留 v1.1，停止在 target/controller 方向继续叠补丁。下一轮应直接聚焦 support formation 质量本身：

1. 分析 fulltest39 中每个 1 条 real strong support 的样本为什么没有形成第二条 independent support；
2. 对比 evidence raw output 与最终 state，确认 evidence 是没抽出来、被降级、被覆盖，还是因为 evidence_map 容量/merge 规则丢失；
3. 若要改 runtime，优先做 Evidence extraction / evidence retention 层面的最小修复，不回到 sticky/throttle/support-pass/final-decision 阈值。
