# Support Formation Pass v1 冒烟结果

## 冒烟目的

确认 support formation pass 是否真实触发，并且触发后是否真的进入 Evidence Agent，而不是被 recovery phase / finalize phase 后置逻辑覆盖。

## 发现的问题与修复

冒烟阶段发现两个实现问题：

1. `normalize_manager_payload()` 会丢弃 `support_formation_pass_triggered / reason / from_action` 字段，导致 runner trace 中可见触发，但 turn log 统计仍为 0。
2. `_apply_recovery_phase_protocol()` 在 pre-worker 与 post-finalize 阶段会重新解释 action，导致 support formation intent 被恢复成 `challenge_previous_hypothesis` 或 `finalize`。

已修复：

- `normalize_manager_payload()` 保留 support formation 日志字段。
- `_apply_recovery_phase_protocol()` 对 support formation pass 直接保留 `verify_evidence`、`normal_review`、`normal_evidence`。

## 4 条冒烟结果

第一次完整冒烟后：

- support pass 真实触发。
- 触发 turn 正确进入 Evidence Agent。
- fallback strong support 没有增加。
- real-claim strong support 有增长，但未达到 2+ real strong support。

## 冒烟结论

Support Formation Pass v1 的执行链路是通的，可以进入 16 条 mixed subset 做正式验证。但 4 条冒烟已经提示：这项改动主要提升 positive evidence formation，不会单独解决 always-reject。
