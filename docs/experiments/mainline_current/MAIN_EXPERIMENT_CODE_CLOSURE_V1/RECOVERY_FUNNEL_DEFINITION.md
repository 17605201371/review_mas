# RECOVERY_FUNNEL_DEFINITION

## 目标

Recovery 在论文中定位为结构化状态修复与诊断模块，不作为当前主性能增益。主试验中不追求提高 commit 数，而追求 recovery 安全、failure code 清楚、commit 后状态不变差。

## Funnel 定义

- `attempted`：worker 输出可解析为 recovery payload，或显式 blocked。
- `emitted`：本 turn 产生 recovery patch / blocked / salvaged patch。
- `validated`：validator 完成检查并返回结构化 failure/success；blocked 也可 validated。
- `committed`：validator 允许并实际写入 ReviewState。
- `blocked`：显式 blocked 或 validator 拒绝 commit。
- `no_effect`：patch 目标已经处于目标状态。
- `negative_commit`：commit 后造成 unsupported_with_strong_support、错误降级或 failure echo。
- `consistency_improved_commit`：commit 后减少真实冲突、降低 ungrounded flaw 或修复 stale state，并且没有新增 contradiction。

## 主试验口径

报告 `attempted/emitted/validated/committed/blocked/no_effect`，但不要把 commit count 当主指标。更重要的是：`negative_recovery_commit_count=0`、`recovery_failure_echo_count=0`、failure code 分布可解释。
