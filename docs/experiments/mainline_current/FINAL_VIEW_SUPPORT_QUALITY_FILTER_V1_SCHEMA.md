# Final-View Support Quality Filter v1 Schema

## 定位

本轮只做离线 final-view simulation，不改 runtime、不改 ReviewState、不改变已有 final report。

## 目的

前面的 negative blocker formation 在 false accept 上覆盖不足，因此本轮不再继续强造负面 blocker，而是检查是否可以通过更严格的正向证据质量过滤，减少 false accept。

## 输入信号

- `real_strong_support_total`
- `non_abstract_support_total`
- `independent_support_group_total`
- `empirical_support_total`
- `claims_with_method_plus_result_support`
- `positive_grounded_criteria`
- `confirmed_critical_flaw_count`
- `grounded_major_flaw_count`
- `grounded_weak_core_criteria`

## 规则边界

这些规则只用于论文分析和下一轮方向判断。不能直接作为 runtime accept/reject 规则。
