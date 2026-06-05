# Final Recommendation Report v1 Decision

## 结论

建议保留为论文层 final-view report rendering。它解决的是“最终报告如何诚实表达系统证据状态”的问题，不解决也不试图替代 runtime accept/reject。

## 关键数字

- accept_like: `1`
- borderline_positive: `12`
- borderline_insufficient: `3`
- reject_like: `1`
- not_assessable: `22`

## 判断

本轮说明当前系统最可信的输出不是硬二分类，而是证据约束下的多类推荐视图。论文主试验可以继续报告 accept/reject health check，但主叙事应转向 recommendation calibration、support quality 和 criterion grounding。

## 下一步

如果继续推进，应做 `Mainline-Final-v1` 结果表整合：把 runtime evidence/state 指标、criterion grounding、final recommendation view 放进同一张主表，而不是继续新增 controller。
