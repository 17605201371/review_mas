# Next Cut After Calibration Decision

## 当前判断

high-precision 已恢复 `2` 个 accept；balanced-only false-accept risk 有 `2` 个。剩余 gold accept 中仍有 `6` 个没有进入 positive recommendation。

这说明下一步不是继续调 final recommendation 阈值，而是补上两类上游证据：empirical evidence formation 和 hard-negative grounding。

## 下一刀选择

优先做 `Empirical Evidence Targeted Audit/Pass v1`，但先保持离线审计，不直接改 runtime。原因：

1. false accept risk 的共同缺口是 empirical support 或 empirical grounded criterion 不足。
2. high-precision 恢复 accept 依赖 empirical adequacy grounded positive，而不是单纯 support count。
3. 4B 上 calibration 恢复 0 accept，说明上游 positive support formation 仍不足。

## 暂时不做

- 不继续调 accept/reject 阈值。
- 不把 balanced 规则直接映射 accept。
- 不恢复 sticky/throttle/gate。
- 不做蒸馏。

## 如果继续实现

下一轮应只做一个小切口：让 Evidence/criterion final-view 分析更可靠地区分 empirical/result/table support 与 abstract/method-only support，并对 reject 样本补 hard-negative grounding case study。
