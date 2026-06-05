# Criterion Decision Next Step

## 当前结论

离线模拟确认了一个负结论：最终推荐确实不能只看 strong support 数量，但当前这版 criterion-grounded aggregation 也不能接入 runtime decision。它能把结果拆成 `accept_like / reject_like / borderline / not_assessable`，但没有恢复任何 gold accept，并且在 accept-like 分支上产生了 false accept。

因此，criterion 现在只能作为论文评估与报告诊断层，不能作为接收/拒收聚合规则。

## 本轮发现

- Sim 1 的 strong-support-count rule 仍然恢复不了 accept，说明单纯 support 数量不是 paper-level 接收标准。
- Sim 2 的 criterion-gated reject 最安全：false accept 为 0，reject recall 为 1.0，但 accept recall 仍为 0；它更适合作为“安全拒绝/不可评估”审计，而不是恢复 accept 的规则。
- Sim 4 的 combined rule 在 strict 映射下仍产生 5 个 false accept，且 recovered accept 为 0；说明当前 criterion 信号和 support-quality 信号还不足以安全推动 accept-like decision。
- 当前 final reports 中的 criterion positive wording 仍然偏弱、偏浅，不能作为论文级 accept 的充分依据。

## Sim 4 安全下界

- accuracy: 0.6667
- macro_f1: 0.5477
- accept_recall: 0.3333
- reject_recall: 0.7667
- predicted_accept_count: 10
- predicted_borderline_count: 6
- false_accept_ids: ye3NrNrYOY, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, WLgbjzKJkk, aTBE70xiFw, kam84eEmub
- recovered_accept_ids: KI9NqjLVDT, 1HCN4pjTb4, BXY6fe7q31

## 下一步建议

下一步不应 runtime 化 criterion-grounded final decision，也不应继续调 final decision 阈值。建议保持 **audit-only**：

1. criterion 继续用于 final report 丰富度、coverage、grounding 和 meta-leakage 审计。
2. final decision 暂时仍不要接入 novelty / soundness / empirical adequacy 等维度。
3. 后续如果要让 criterion 进入决策，必须先提高 criterion assessment 的 grounding 质量，并证明它能恢复 gold accept 且不制造 false accept。
4. 近期更值得做的是补强 evidence/support quality 与 criterion grounding，而不是增加新的 controller 或 decision rule。

## 暂时不要做

- 不要让模型自由拍板 final decision。
- 不要写 `low novelty -> reject` 或 `criterion positive -> accept` 的硬规则。
- 不要让 ungrounded candidate flaw 触发强 reject。
- 不要把 not_assessable 当作 paper weakness。
- 不要把本轮 Sim 4 当成可以上线的 final-view decision rule。
