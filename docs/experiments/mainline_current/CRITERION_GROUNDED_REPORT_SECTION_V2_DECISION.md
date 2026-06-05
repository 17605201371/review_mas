# Criterion-Grounded Report Section v2 Decision

## 当前结论

本轮可以保留为离线 report-layer 改进。它没有修改 final decision，但让 criterion section 从纯文本/关键词式维度描述，变成了 evidence/flaw-linked 的 grounded view。

## 价值

1. 论文中可以展示 novelty / significance / soundness / empirical / clarity 五个审稿维度。
2. 每个维度明确区分 `positive_grounded`、`negative_grounded`、`mixed_grounded` 和 `not_assessable`。
3. 无 grounding 的维度不会被写成论文 weakness，降低 meta/excerpt limitation 误写风险。

## 限制

1. 这仍是离线渲染，不代表模型推理本身更强。
2. criterion grounding 仍依赖现有 evidence/flaw 质量；如果 evidence formation 不足，criterion section 会大量 not_assessable。
3. 不允许把本轮输出接入 accept/reject。

## 下一步建议

如果继续推进主线，应回到 evidence/support quality：提升 non-abstract、empirical、independent support formation。criterion report v2 作为论文展示层保留，不再继续叠 decision rule。
