# Soft Negative Extraction Series Decision

## 结论

本轮验证了 `Hard-Negative Extraction` 作为下一步的可能性，但结果不支持把它直接接入 runtime 或 final decision。

## 对比

| run | false_risk_rows | false_risk_trusted_blocker_rows | accept_protect_rows | accept_trusted_blocker_rows | false_risk_weak_negative_rows | parse_error_rows_total |
| --- | --- | --- | --- | --- | --- | --- |
| 4B v1.4 / 6144 context | 7 | 3 | 2 | 0 | 5 | 0 |
| 9B v1.4 / 3072 context | 7 | 0 | 2 | 0 | 1 | 2 |
| 9B compact v1.1 / 3072 context | 7 | 0 | 2 | 0 | 2 | 7 |

## 解释

- 4B v1.4 在 7 个 false-accept-risk 样本中找到 3 个 trusted blocker，同时没有误伤 2 个 recovered accept。这说明任务有潜在价值。
- 9B v1.4 没有形成 trusted blocker，主要输出 `not_assessable`，且有 parse error。
- 9B compact v1.1 没有改善，parse error 反而上升，说明问题不是单纯 prompt 长度，而是当前结构化 hard-negative extraction 对 9B 仍不稳定。

## 决策

`Hard-Negative Extraction` 暂时保留为离线 / human-review 辅助层，不进入 runtime、不进入 final decision。正式论文口径仍应保持：

- `accept_like` 可以作为高置信推荐信号；
- `borderline_positive` 不能直接映射成 accept；
- `not_assessable` 是独立输出，不是 accept 或 reject；
- hard-negative extraction 只能作为 case study 或人工复核证据，不能作为自动 reject blocker。

## 下一步

停止继续调 hard-negative prompt。下一步应转向主试验收口：冻结 `Mainline-Final-v1` 结果包，整理 9B fulltest39 的论文主表和 case study，而不是继续追加 controller 或 prompt family。
