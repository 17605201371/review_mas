# FINAL_RECOMMENDATION_VIEW_RUNTIME_V1

## 定位

本轮修复的是 final decision 层的口径问题，不是继续调 Evidence Agent、recovery、sticky、throttle 或 progression gate。

旧问题是：`infer_final_decision(...)` 只有二分类输出，并且直接用 unresolved / flaw / conflict 的硬阈值压制 positive support，导致 runtime decision 长期 collapse 成 reject。

新方案是：

> 先生成 evidence-grounded `final_recommendation_view`，再把 strict `accept_like` 保守映射为 binary accept；其余 `borderline_*`、`not_assessable_*`、`reject_like` 都不强行映射为 accept。

这不是“放松 reject 阈值”，而是把 final decision 从单层硬规则改成：

1. support quality；
2. grounded hard-negative；
3. uncertainty / targetless unresolved；
4. conservative binary projection。

## 新增接口

`agent_system/environments/env_package/review/state.py` 新增：

```python
infer_final_recommendation_view(state, manager_payload)
```

输出字段包括：

- `recommendation_view`
- `binary_decision`
- `reason`
- `real_strong_support_total`
- `non_abstract_real_strong_support_count`
- `empirical_real_strong_support_count`
- `open_unresolved_count`
- `targetless_uncertainty_count`
- `grounded_major_flaw_count`
- `grounded_critical_flaw_count`

`infer_final_decision(...)` 现在只是这个 view 的 conservative binary projection：只有 `accept_like` 返回 `accept`。

## 规则原则

### accept_like

必须满足：

- real-claim strong support 足够；
- non-abstract support 足够；
- empirical/method support 足够；
- 没有 grounded critical / major blocker；
- 没有 open unresolved；
- 如果仍有 targetless uncertainty，必须有更高置信度的 real empirical support。

### borderline_positive

存在明显正向 support，但仍有 targetless uncertainty 或未验证负面项。它不映射为 accept。

### borderline_insufficient

有一些 real support，但 support quality、coverage 或独立性不足。

### not_assessable_uncertain

缺少可用 positive support，同时 unresolved/targetless uncertainty 较高。

### reject_like

存在 grounded major/critical blocker，或缺少 usable accept support。

## 现有 9B fulltest39 离线对照

输入：

`outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_fulltest39_merged_gold_20260503.jsonl`

结果：

| metric | value |
| --- | ---: |
| row_count | 39 |
| accept_like | 1 |
| borderline_positive | 2 |
| borderline_insufficient | 24 |
| not_assessable_uncertain | 11 |
| reject_like | 1 |
| binary_accept | 1 |
| binary_reject | 38 |
| recovered_accept_ids | `jVEoydFOl9` |
| false_accept_ids | none |

## 结论

最终决策不是修不好，而是不能继续靠单层硬阈值修。

这轮改动使 runtime 层具备了论文所需的 recommendation view：能安全恢复 1 个 accept-like 样本，同时保持 0 false accept，并保留 borderline / not-assessable 作为审稿辅助系统的真实不确定性表达。

下一步如果继续提升，不应再调 binary threshold，而应提升 hard-negative grounding 和 criterion assessment 的质量。
