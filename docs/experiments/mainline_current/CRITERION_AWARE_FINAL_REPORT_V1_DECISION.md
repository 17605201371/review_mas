# Criterion-Aware Final Report Section v1 决策

## 结论

保留本轮改动。

## 原因

本论文项目目标不是单纯预测 accept/reject，而是构建一个 evidence-grounded 的多轮审稿辅助系统。旧版最终报告包含 Summary、Strengths、Weaknesses、Questions 和 Reason，但没有稳定覆盖 novelty、soundness、empirical adequacy、clarity 等真实审稿维度。

本轮改动补齐了最终报告的审稿维度结构，同时保持现有 decision 路径不变。因此它提升的是报告完整性和论文呈现，不会引入新的接收/拒绝判定风险。

## 解决的问题

- 增加显式 novelty/originality 评估。
- 增加显式 significance/contribution 评估。
- 增加显式 technical soundness 评估。
- 增加显式 empirical adequacy 评估。
- 增加显式 clarity/reproducibility 评估。
- 对缺少 grounding 的维度使用 `not_assessable` 或保守表述，不直接写成论文 weakness。

## 没有解决的问题

- 不提升 evidence formation。
- 不修复 false accept / false reject。
- 不改变 recovery commit 质量。
- 不替代 support quality 或 flaw lifecycle 工作。

## 下一步

完成报告层补齐后，下一轮 runtime 相关工作仍应回到 evidence/support quality，重点提升 non-abstract、empirical、independent support formation。暂时不要把 criterion label 直接接入 final decision。
