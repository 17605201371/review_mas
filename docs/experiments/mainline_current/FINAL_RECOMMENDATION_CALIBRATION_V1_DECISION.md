# Final Recommendation Calibration v1 Decision

## 结论

本轮确实弥补了 accept collapse 的一部分，但不能把问题包装成已经解决。

在 9B fulltest39 dry-run 上：

- `calibrated_high_precision` 恢复 `2` 个 accept，false accept `0`，accept precision `1.0`。
- `calibrated_balanced` 恢复 `3` 个 accept，但 false accept `2`。

因此，推荐口径是：

> high precision 通过的样本标为 `accept_like`；balanced 通过但 high precision 不通过的样本标为 `borderline_positive`，不直接映射 accept。

## 为什么这能弥补当前短板

原始 runtime final decision 是 all reject。高精度校准至少能恢复一部分有实证/criterion 支撑的 accept，同时避免 false accept。balanced 规则能提高 accept recall，但会引入 false accept，所以只能作为 borderline 发现器。

## 4B 的含义

4B mainline fulltest39 上 `calibrated_high_precision` 恢复 `0` 个 accept。4B 的主要问题不是聚合规则，而是上游 positive support formation 不足；不能靠 final calibration 单独弥补。

## 保留 / 不保留

保留：

- `calibrated_three_way` 作为论文 final recommendation view 的校准口径。
- `calibrated_high_precision` 作为 strict accept-like 映射。
- `calibrated_balanced` 作为 borderline-positive 发现器。

不保留：

- 不把 balanced 直接映射为 accept。
- 不把 support count 单独作为 accept 规则。
- 不改 runtime final decision。

## 下一步

1. 将 `Final Recommendation Calibration v1` 写入主结果包。
2. 如果要做正式主试验，用 `calibrated_three_way` 报告 recommendation view；binary accept/reject 只作为 health check。
3. 继续保留 false accept case study，尤其检查 balanced-only 样本为何风险高。
