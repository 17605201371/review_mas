# Criterion Grounding Linker v1 Decision

## 当前结论

本轮 linker 支持继续把 criterion 放在报告与审计层，而不是接入 final decision。它能把 final report 的维度提及和 `ReviewState` 中的 evidence / flaw grounding 对齐，但也显示当前 criterion grounding 仍不够稳定，尤其不能把 positive criterion 作为 accept-like 信号。

## 核心统计

- rows: `39`
- positive grounded criterion links: `32`
- negative grounded criterion links: `15`
- report-only criterion mentions: `80`
- not-assessable criterion labels: `14`

## 解释

1. criterion 维度可以提升论文报告的“审稿维度饱满度”，也能帮助识别 novelty / significance / soundness / empirical / clarity 是否有证据支撑。
2. 但是当前 grounding 多数仍依赖已有 evidence/flaw 的粗粒度匹配，不能证明 paper-level accept。
3. 因此不要把 criterion linker 输出接入 accept/reject，也不要写 `positive criterion -> accept` 规则。
4. 下一步如果继续推进 report 层，应做 `Criterion-Grounded Report Section v2`：用 linker 结果渲染 criterion section，确保无 grounding 的维度写成 not_assessable，而不是 weakness。

## 下一步唯一建议

建议下一步做 **Criterion-Grounded Report Section v2**，仍保持 report-only：

- 用 linker 结果替代纯关键词式 criterion section。
- 每个 criterion 明确列出 linked evidence / linked flaw / not_assessable reason。
- 不改 final decision。

## 暂时不要做

- 不要 runtime 化 criterion-grounded decision。
- 不要继续调 accept/reject 阈值。
- 不要回到 sticky/throttle/progression gate。
