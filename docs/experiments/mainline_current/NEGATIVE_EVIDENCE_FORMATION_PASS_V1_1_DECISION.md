# Negative Evidence Formation Pass v1 Decision

## 结论

不直接保留为决策模块，先分析误伤/漏检。

## 关键数字

- false accept trusted_blocker_rows: `1 / 7`
- recovered accept trusted_blocker_rows: `0 / 3`
- false accept parse_error_rows: `3`

## 判断

如果 false accept 与 recovered accept 都大量形成 trusted blocker，则说明当前 pass 能找负面线索，但缺少 discriminative confirmation，不能直接用于 reject。

下一步只允许做两类小修：

1. 收紧 trusted blocker 条件，要求 paper anchor 更具体。
2. 对 recovered accept 的 blocker 做 precision audit，找出误伤来源。

暂时仍不改 final decision 阈值。
