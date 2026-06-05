# Final Recommendation View v1 Decision

## 结论

建议把下一阶段的 final-view 输出从硬二分类改成四类/五类推荐视图，而不是继续调 accept/reject 阈值。

## 关键数字

- accept_like: `1`
- borderline_positive: `12`
- reject_like: `1`
- not_assessable: `22`
- accept_like gold 分布: `{'accept': 1}`

## 判断

当前证据链支持高精度 accept-like，但不支持高召回二分类 accept。负向 blocker formation 覆盖不足，因此不应为了压 false accept 继续硬造 blocker。

下一步应做 `Final Recommendation View v1` 的论文层整合：

1. runtime final decision 仍作为 health check。
2. final-view report 输出 `accept_like / borderline_positive / reject_like / not_assessable`。
3. `borderline_positive` 不映射为 accept，用于展示系统可诊断的不确定性。
