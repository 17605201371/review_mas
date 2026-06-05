# Support Provenance Reconciliation v1

## 需要区分的三个口径

1. `raw_fallback_strong_support`: raw ReviewState 中存在的 fallback-bound strong support，通常绑定 `claim-fallback-*`，只作为污染/残留指标。
2. `decision_real_strong_support`: criterion/support simulation 中使用的真实 claim strong support，排除 fallback/general claim。
3. `recommendation_eligible_support`: final recommendation view 使用的 support quality 信号，必须是真实 claim、non-abstract/independent/criterion-grounded 的派生信号。

## 本轮判断

- raw fallback strong 仍存在，说明 runtime state 还保留早期 fallback 产物。
- 这些 fallback strong 没有进入 `accept_like` 样本；`accept_like_rows_with_raw_fallback_strong=0`。
- 因此 Evidence Binding 的论文结论应表述为：final-view/recommendation 层已经隔离 fallback strong，而不是 raw state 已经完全没有 fallback strong。

## 写论文时的建议表述

> We retain raw fallback-bound support as a diagnostic signal, but exclude it from decision-eligible real-claim support and final-view recommendation aggregation.
