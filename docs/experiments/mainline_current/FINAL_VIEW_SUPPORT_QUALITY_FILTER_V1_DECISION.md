# Final-View Support Quality Filter v1 Decision

## 结论

本轮是离线模拟。它的作用是判断是否该把下一步从 negative blocker formation 转向 positive support sufficiency。

## 关键观察

- high_precision false_accept_count: `0`
- high_precision recovered_accept_count: `1`
- high_precision accept_recall: `0.1111`
- high_precision reject_recall: `1.0`
- best_macro_f1_rule: `sqf_two_positive_criteria`

## 判断

如果 stricter support quality filter 能显著降低 false accept，但 true accept 也被压得太低，说明当前不能直接 runtime 化 accept 规则。

下一步应做：

1. 保留 support quality 作为 final-view 诊断指标。
2. 继续把 `borderline / needs_human_review` 作为推荐层输出，而不是强行二分类。
3. 不再继续追求 negative blocker pass 覆盖所有 false accept；当前可见上下文不足以稳定确认这些 blocker。
