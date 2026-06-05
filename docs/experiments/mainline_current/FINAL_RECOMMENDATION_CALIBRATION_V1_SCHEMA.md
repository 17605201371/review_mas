# Final Recommendation Calibration v1 Schema

## 目标

本轮弥补 runtime accept collapse，但不直接改 runtime。校准只发生在 final-view / offline 层，用已有 support quality、criterion grounding、flaw lifecycle 信息重新聚合 recommendation。

## 为什么不能只调 strong support 数量

`real_strong_support_total >= 2` 会恢复更多 accept，但在 9B fulltest39 上会产生大量 false accept。原因是 strong support 仍可能只是局部 claim 成立，不等于 paper-level accept。

## 两个校准口径

### calibrated_high_precision

用于高精度 `accept_like`：

- `sim4_label` 为 `accept_like` 或 `borderline`；
- 无 confirmed critical flaw、grounded major flaw、core weak criterion；
- 无 negative evidence；
- real strong support >= 2；
- non-abstract support >= 1；
- independent support groups >= 2；
- positive grounded criteria >= 2；
- empirical support >= 1 或 empirical criterion grounded positive。

### calibrated_balanced

用于召回更多潜在 accept，但风险较高：

- 满足 high precision 的所有条件，除了 empirical support / empirical criterion 约束。

### calibrated_three_way

- high_precision 通过 -> `accept_like`；
- balanced 通过但 high_precision 不通过 -> `borderline_positive`；
- 其余按 not_assessable / borderline_insufficient / reject_like 保留。

## 使用边界

`calibrated_balanced` 不能直接作为正式 accept 规则；它用于发现 borderline positive。正式论文主口径应优先使用 `calibrated_three_way`。二分类 accuracy 只作为 health check。
