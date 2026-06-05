# Criterion Decision Next Step

## 当前结论

这轮结果必须分 4B fulltest39 和 9B confirmation 两层读：

- 在 4B fulltest39 上，criterion-grounded aggregation 仍不能恢复 accept，说明 4B 的 positive support / criterion grounding 仍不足。
- 在 9B confirmation subset 上，criterion-grounded aggregation 能恢复 4/5 个 accept，但误翻 1 个 reject（`kam84eEmub`）。

因此，criterion 不是没有价值；相反，它说明 9B 产生的 real support 已经可以被 final-view policy 使用。但当前 policy 还缺 false-accept safety constraints，不能直接 runtime 化。

## 关键读法

- 不要回到 strong-support-count rule。
- 不要让模型自由输出 final decision。
- 不要把 novelty/soundness/empirical 低分直接变成 reject。
- 不要把 criterion aggregation 直接接进 runtime。

## 下一步建议

下一步唯一建议是：`Final Recommendation Policy v1 Safety Simulation`。

目标是在不跑模型、不改 runtime 的前提下，对 `kam84eEmub` 这类 false accept 风险加安全约束：

1. empirical support 为 0 时不能直接 accept_like；
2. abstract/self-claim-only support 不能直接 accept_like；
3. positive criterion 必须 evidence-grounded；
4. not_assessable 不作为 weakness，也不作为 accept；
5. grounded empirical/soundness blocker 优先级高于 support 数量。

只有 safety simulation 同时满足“恢复 accept + false accept 受控”，才进入 9B fulltest dry run。
