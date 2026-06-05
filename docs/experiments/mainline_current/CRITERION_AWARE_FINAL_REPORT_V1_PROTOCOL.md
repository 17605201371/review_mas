# Criterion-Aware Final Report Section v1 协议

## 目标

在不改变 runtime 决策逻辑的前提下，为最终审稿报告增加显式审稿维度章节。

## 范围

本轮只修改 `render_final_review(...)` 的最终报告渲染。

本轮不修改：

- `infer_final_decision(...)`
- recovery / sticky / throttle / progression gate / manager policy
- evidence binding / state merge / lifecycle / reward
- accept/reject 阈值

## 审稿维度

最终报告现在固定渲染五个维度：

- Novelty / Originality
- Significance / Contribution
- Technical Soundness
- Empirical Adequacy
- Clarity / Reproducibility

每个维度输出以下状态之一：

- `positive`
- `negative`
- `mixed`
- `not_assessable`

当有 grounding 时，报告会引用 claim/evidence id。缺少 grounding 时，报告应输出 `not_assessable` 或保守表述，而不是把系统不确定性写成论文缺陷。

## 设计原因

离线 criterion audit 显示 fulltest39 的最终报告平均只覆盖约 2.41 个审稿维度，其中 novelty 与 clarity 覆盖最低。增加结构化审稿维度章节可以让报告更像真实审稿表，同时不会引入新的 decision 不稳定来源。

## 护栏

criterion 输出只用于报告呈现和论文分析。除非 evidence binding、support quality、state hygiene、flaw lifecycle 已经稳定，否则不允许让这些维度直接影响 accept/reject。
