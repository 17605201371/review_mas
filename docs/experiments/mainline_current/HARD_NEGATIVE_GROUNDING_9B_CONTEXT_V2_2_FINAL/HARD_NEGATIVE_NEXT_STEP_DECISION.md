# Hard-Negative Next Step Decision v1

## 结论

当前 reject 样本的主要缺口不是 positive support，而是 hard-negative grounding。30 条 gold reject 中，final-view 分布为：{'borderline_positive': 13, 'not_assessable': 15, 'reject_like': 1, 'borderline_insufficient': 1}。

## 主导问题

| dominant_gap | count |
| --- | --- |
| negative_unresolved_not_promoted | 13 |
| insufficient_positive_and_negative_grounding | 9 |
| meta_burden_masks_missing_hard_negative | 7 |
| has_grounded_major_or_critical | 1 |

## 对 recommendation 的含义

`borderline_positive` 不能升级为 `accept_like`，因为大量 gold reject 同时具有 real/non-abstract/empirical support。要想恢复安全的 accept-like，必须先证明 reject 样本的真实 hard-negative 能被抽取并 grounded；否则任何 support-only accept 规则都会制造 false accept。

## 下一步唯一建议

`Hard-Negative Extraction v1`，但只应先在离线/prompt 层小样本验证：让 critique / criterion report 明确抽取 empirical weakness、soundness weakness、novelty/significance weakness，并要求 evidence/claim grounding。不要改 runtime final decision，不要回 controller。
