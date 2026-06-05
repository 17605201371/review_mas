# Criterion Grounding Linker v1 Schema

本轮是离线 grounding linker，不改 runtime、不改 final decision、不重跑模型。

## 目的

上一轮 criterion-grounded decision simulation 说明：criterion 信号现在不能安全接入 accept/reject。v1 linker 的目标不是决策，而是把 criterion 维度和已有 `ReviewState` 中的 evidence / flaw 建立可追踪关系，区分：

- report text 提到了某维度；
- 该维度是否能从 state evidence / grounded flaw 得到支撑；
- 该维度是 positive grounding、negative grounding、not-assessable，还是 report-only；
- 是否存在 meta leakage。

## 五个维度

- novelty_originality
- significance_contribution
- technical_soundness
- empirical_adequacy
- clarity_reproducibility

## 关键字段

- `criterion_state_grounded_*`: 该维度至少有真实 claim evidence 或 grounded flaw 绑定。
- `criterion_positive_grounded_*`: 该维度有正向 evidence 绑定。
- `criterion_negative_grounded_*`: 该维度有负向 evidence 或 grounded flaw 绑定。
- `criterion_report_only_*`: final report 提到该维度，但 state 中没有找到 grounding。
- `criterion_not_assessable_*`: 该维度缺少 grounding，应当报告为无法评估，而不是论文缺陷。

## 约束

该 linker 只用于审计和后续 report section 改进，不允许直接驱动 final decision。
