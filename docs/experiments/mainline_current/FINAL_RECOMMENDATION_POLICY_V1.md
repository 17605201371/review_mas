# Final Recommendation Policy v1

## 定位

`Final Recommendation Policy v1` 是论文主线里的 final-view aggregation 规范，不是 runtime prompt，也不是 live ReviewState mutation。它的目标是把 ReviewState、support quality、flaw lifecycle、criterion grounding 组合成可解释的 recommendation view。

本策略不让模型自由拍板 accept/reject，也不使用单纯 strong-support-count 规则。

## 输出标签

最终推荐先使用四类：

- `accept_like`
- `reject_like`
- `borderline`
- `not_assessable`

二分类 accuracy 只作为 health check。论文主指标应报告 evidence/support quality、criterion grounding、flaw lifecycle 与 meta-leakage。

## 强 reject 条件

只有以下信号可形成强 reject：

1. grounded confirmed critical flaw；
2. grounded major soundness flaw；
3. grounded major empirical adequacy flaw；
4. core claim 被 grounded contradiction 反证；
5. 多个核心 criterion 为 weak 且 grounded。

以下信号不能强 reject：

- ungrounded candidate flaw；
- fallback / malformed artifact；
- excerpt limitation；
- system/meta limitation；
- not_assessable criterion；
- stale evidence gap。

## accept_like 条件

`accept_like` 必须同时满足：

1. 无 confirmed critical flaw；
2. 无 grounded major soundness/empirical blocker；
3. 至少 `2` 个 real-claim strong support；
4. 至少 `1` 个 non-abstract support；
5. 至少 `2` 个 independent support groups；
6. 至少一个正向 criterion grounded，例如 novelty/significance/soundness/empirical 中的 positive grounded assessment；
7. fallback-bound strong support 不计入 accept 条件。

## false-accept safety constraints

9B confirmation 中 `kam84eEmub` 是关键风险：它有 high support 和 positive criterion wording，但 gold 是 reject。因此 v1 还需要以下 safety gate：

- 如果 support 主要是 abstract/self-claim，不能 accept_like；
- 如果 empirical support 为 0 且 paper decision 依赖 empirical adequacy，应降为 `borderline`；
- 如果 positive criterion 只来自 final report 泛化措辞，缺少 evidence/section grounding，应降为 `borderline`；
- 如果 reject-side review 有高评分但 gold reject，应优先检查是否存在 hidden empirical/soundness blocker，而不是直接 accept_like。

## not_assessable 条件

当关键 criterion 缺少上下文或 evidence 时，应输出 `not_assessable` 或 `borderline`，而不是把系统限制写成 paper weakness。

## 当前实验判断

- 4B fulltest39: criterion-grounded aggregation 仍不能恢复 accept，说明 4B positive support/criterion grounding 不足。
- 9B confirmation: strict 映射恢复 4 个 accept，但产生 1 个 false accept；lenient 映射恢复 5 个 accept，但同样有 1 个 false accept。

因此，policy 方向成立，但不能直接上线为 runtime decision。下一步应做 `Final Recommendation Policy v1 Safety Simulation`：专门围绕 false accept case 加 safety constraints，并在 9B confirmation + 4B fulltest39 上离线验证。


## Safety Simulation Update

`Final Recommendation Policy v1 Safety Simulation` 支持加入第一条安全约束：如果存在 `negative_evidence_total > 0`，则不得直接输出 `accept_like`，应降为 `borderline`。该约束在 9B confirmation subset 上把 false accept `kam84eEmub` 从 accept_like 降为 borderline，同时保留主要 recovered accept。当前仍不建议 runtime 化，只作为 final-view/offline recommendation policy。
