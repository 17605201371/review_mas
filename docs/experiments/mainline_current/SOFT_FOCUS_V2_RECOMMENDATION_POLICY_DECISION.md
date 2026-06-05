# Soft Focus v2 Recommendation Policy Decision

## 结论

`Soft Evidence Focus v2` 的 evidence formation 可以保留，但 runtime binary final decision 不能保留为主判断。应使用 hard-negative-aware 的 final recommendation view。

## 最稳规则

`high_precision_criterion_quality` 是当前最稳的离线规则：

- recovered accept: LebzzClHYw
- false accept: none
- accept recall: 0.1111
- reject recall: 1.0
- macro-F1: 0.5412

该规则恢复较少，但能挡住 runtime false accept `NnExMNiTHw`。它要求 support 不只是 result 数量足够，还必须有 method support，并且 novelty / technical soundness / empirical adequacy 都是 positive。

## Recommendation view 分布

当前视图分布：{'reject_like': 5, 'not_assessable': 15, 'borderline_insufficient': 9, 'borderline_positive': 9, 'accept_like': 1}

- `accept_like`: 高精度、可映射 accept 的样本。
- `borderline_positive`: 有正向 support，但缺少 method/soundness/novelty 或 hard-negative 仍不清楚，不能映射 accept。
- `reject_like` / `not_assessable`: 不应硬转 accept。
- `borderline_insufficient`: 证据或 criterion 条件不足，单独保留为诊断状态。

## 下一步

1. 将 `high_precision_criterion_quality` 作为论文中的 strict accept-like 口径。
2. 将 `borderline_positive` 单独报告，不映射为 accept。
3. 不再继续调 runtime final decision 阈值；runtime accept/reject 只作为 health check。
4. 下一轮若要提升 recall，应优先改善 method/soundness evidence formation，而不是放宽 high-precision rule。
