# Final Recommendation Policy v3 9B Context v2.2 Final

## 结论

当前不应把 final recommendation 收敛成二分类 accept/reject，也不应把 `borderline_positive` 自动映射成 accept。`Final Recommendation Policy v3` 冻结为保守四分类：

- `reject_like`: 只在存在 grounded major/critical hard-negative 时使用。
- `borderline_positive`: 有 real / non-abstract / empirical support，但 hard-negative 尚未充分排除。
- `not_assessable`: unresolved / context limitation / targetless questions 较高，无法可靠推荐。
- `borderline_insufficient`: 有少量信号但 support 或 grounding 不足。

## 为什么不能 support-only accept

最新 9B run 中：

| metric | value |
| --- | --- |
| real_strong_support_total | 49 |
| nonabstract_strong_support_total | 49 |
| empirical_strong_support_total | 38 |
| fallback_strong_support_total | 0 |
| rows_with_2plus_real_strong_support | 17 |
| runtime_predicted_accept_count | 0 |
| runtime_accept_recall | 0.0 |

positive support 已经形成，但 runtime 仍 39/39 reject。另一方面，reject 样本里也大量存在 high-quality support。如果把 support-only rule 当 accept，会产生 false accept 风险。

## Hard-Negative Grounding 证据

30 条 gold reject 的 dominant gap：

| dominant_gap | count |
| --- | --- |
| has_grounded_major_or_critical | 1 |
| insufficient_positive_and_negative_grounding | 9 |
| meta_burden_masks_missing_hard_negative | 7 |
| negative_unresolved_not_promoted | 13 |

推荐视图分布：

| view | count |
| --- | --- |
| borderline_insufficient | 1 |
| borderline_positive | 13 |
| not_assessable | 15 |
| reject_like | 1 |

解释：只有 1 条 reject 有明确 grounded major/critical blocker；13 条 reject 的问题是 negative unresolved 没有被提升为 grounded hard-negative；7 条是 meta burden 掩盖 hard-negative 缺失。因此当前最缺的是 hard-negative grounding，而不是继续放宽 accept。

## Policy v3 规则

### reject_like

允许条件：

- grounded major/critical flaw > 0；或
- grounded empirical/soundness blocker 被明确链接到 evidence/claim。

禁止条件：

- fallback/meta flaw 不能触发 reject_like；
- excerpt/context limitation 不能触发 reject_like；
- ungrounded candidate flaw 不能等同 confirmed weakness。

### borderline_positive

条件：

- real strong support >= 2；
- non-abstract support >= 2；
- empirical/result/method support 存在；
- 但 hard-negative 未充分排除。

含义：这是审稿辅助中的“正向但需人工复核”，不自动 accept。

### not_assessable

条件：

- targetless unresolved 多；
- excerpt/context limitation 多；
- negative evidence 未 grounded；
- criterion not assessable。

含义：明确暴露系统/上下文限制，而不是写成论文缺陷或强 reject。

### borderline_insufficient

条件：

- 有少量 support 或 stale/meta burden；
- 但 support quality / criterion grounding / hard-negative grounding 都不足。

## 对论文主试验的影响

正式主表应报告 runtime binary decision 作为 health check，但 final recommendation 主叙事使用四分类 view。这样可以同时解释：

1. 为什么系统不应继续 always-reject；
2. 为什么 support-positive 不能直接 accept；
3. 为什么 hard-negative grounding 是最后收口点；
4. 为什么 final-view report partition 是论文层贡献。

## 下一步

下一步如果继续打磨系统，唯一值得做的是 `Hard-Negative Grounding v2` 的离线/小样本验证：把 negative unresolved 中的 empirical/soundness/novelty concern 链接到 evidence/claim，判断它们是否能成为 grounded blocker。不要改 runtime decision 阈值，不做 controller。
