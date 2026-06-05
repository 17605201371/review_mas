# Criterion-Aware Final Report Section v1 运行决策

## 最终结论

**保留 report-only 改动，不把 criterion 维度接入 final decision。**

## 保留理由

这轮 16 条 4B mixed subset 运行中，16 条 final report 全部生成了 `4. Criterion Assessment`，说明该章节在真实推理输出中可稳定落盘。它解决的是论文呈现和审稿维度覆盖问题：系统现在会显式讨论 novelty、significance、soundness、empirical adequacy 和 clarity，而不是只输出 strengths / weaknesses 的松散文本。

该改动只发生在 final report 渲染层，没有改变 `infer_final_decision(...)`，因此不会给当前 accept/reject 结论引入新的行为风险。

## 不保留为 decision signal 的理由

本轮所有样本仍然输出 reject，说明 criterion section 本身不能解决 always-reject。更重要的是，离线模拟显示 criterion-grounded accept signal 会恢复 2 个 accept，但同时误翻 2 个 reject。因此现在把 novelty / soundness / empirical adequacy 等维度接入 final decision 太早，会把报告维度覆盖误当作接收依据。

## 论文层含义

该改动适合写成：

> 为了让最终审稿报告更符合真实审稿维度，我们在 final report 中增加 criterion-aware section，用于显式报告 novelty、significance、technical soundness、empirical adequacy 和 clarity/reproducibility。该 section 是报告层解释，不参与 accept/reject 决策。

这能回应“审稿维度不够饱满”的问题，同时不偏离项目主线：证据对齐、状态卫生、flaw lifecycle 和最终报告 grounding。

## 当前未解决问题

- always-reject 仍然存在。
- real strong support 仍不足，本轮重跑只有 `real_strong_support_total = 6`。
- unresolved burden 仍高，`unresolved_count = 89`。
- major/critical flaw burden 仍高，`major_or_critical_flaws = 18`。
- criterion section 的覆盖率高，但底层 state/evidence grounding 仍不足。

## 下一步建议

下一步不要继续扩 criterion decision rule。更合理的顺序是：

1. 保留 Criterion-Aware Final Report Section v1。
2. 基于 Evidence Binding Robustness v1，继续检查 positive support formation 是否稳定。
3. 优先推进 final-view hygiene 或 candidate/unresolved lifecycle，目标是减少 stale negative burden，而不是放松 final decision 阈值。
4. criterion 方向后续只做 `Criterion Grounding Linker` 或 report-section refinement，暂时不进入 accept/reject rule。
