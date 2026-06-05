# Final Recommendation Report v1 Protocol

## 定位

本轮是离线 report rendering，不改 runtime、不改 ReviewState、不改变已有 accept/reject。它只把 `Final Recommendation View v1` 的多类推荐结果写入派生 final report。

## 输出标签

- `accept_like`
- `borderline_positive`
- `borderline_insufficient`
- `reject_like`
- `not_assessable`

## 规则边界

- runtime final decision 仍只作为 health check。
- `borderline_positive` 不映射为 accept。
- `not_assessable` 不映射为 reject。
- 本节用于论文层可诊断展示，不是新的决策阈值。
