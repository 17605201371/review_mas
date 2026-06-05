# Final Decision Independent Support Guard v1

## 目标

本修正只保护 runtime binary final decision，避免重复 strong support 或 abstract-only support 将 reject 样本误翻成 accept。

## 背景

`Evidence Empirical Structuring v1` 在 4B fulltest39 上显著增加 empirical strong support：

- `real_strong_support_total: 10 -> 41`
- `nonabstract_strong_support_total: 7 -> 38`
- `empirical_strong_support_total: 7 -> 35`
- `fallback_strong_support_total: 0 -> 0`

但同时出现 2 个 false accept：`ZHr0JajZfH`、`kam84eEmub`。逐样本检查显示问题不是 fallback binding，而是重复或集中于少数 claim 的 result evidence 被 runtime final decision 当成足够独立的 accept 依据。

## 改动

`infer_final_decision(...)` 仍然只是 health-check binary decision，不作为论文主推荐策略。accept 条件从单纯 `real_strong_support_total >= 3 && unresolved <= 3` 收紧为：

- `real_strong_support_total >= 3`
- `claims_with_real_strong_support >= 2`
- `non_abstract_real_strong_support_count >= 2`
- `major_flaws == 0`
- `unresolved <= 1`
- `conflicts == 0`

## 不改内容

- 不改变 final recommendation view。
- 不改变 criterion-aware report。
- 不改变 Evidence Agent 输出。
- 不改变 recovery / state hygiene / fallback。

## 论文解释

accept/reject 仍只作为 health check。正式论文主线应报告 derived recommendation view、support quality、criterion grounding 和 state hygiene，而不是把 binary runtime decision 作为唯一目标。
