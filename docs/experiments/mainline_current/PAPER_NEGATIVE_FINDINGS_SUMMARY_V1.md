# Paper Negative Findings Summary v1

## 负结果 1：后置 controller 不能解决主问题

sticky / throttle / progression gate 多轮实验显示，坏路径通常在 target/evidence/state 更早阶段已经形成。继续叠 controller 容易带来 regression，不适合作为主线。

## 负结果 2：强造 negative blocker 覆盖不足

`Negative Evidence Anchor Extraction v1` 能抽到正文锚点，但 `Anchor Confirmation Pass v1` 在 false accept 上没有形成 trusted blocker，反而误伤 recovered accept。这说明当前 evidence visibility 和 4B confirmation 能力不足以支撑 hard reject blocker。

## 负结果 3：硬二分类会掩盖系统不确定性

criterion/support-based accept 规则可以恢复部分 accept，但 false accept 风险明显；高精度 support filter 可降低 false accept，但召回过低。多类 final-view recommendation 比硬二分类更适合当前论文定位。

## 负结果 4：raw state 仍有 fallback 残留

raw ReviewState 中仍存在 fallback-bound strong support，但 final-view recommendation 已将其排除。论文中应明确区分 raw diagnostic state 和 decision-eligible derived view。
