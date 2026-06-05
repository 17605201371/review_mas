# Final Recommendation Calibration Case Review v1

## 目的

本文件解释 `Final Recommendation Calibration v1` 为什么能部分弥补 all-reject，同时为什么不能把 balanced 规则直接映射成 accept。本轮只做离线 case review，不改 runtime。

## 总览

| paper_id | gold | calibrated_label | diagnosis | real | nonabs | empirical | ind_groups | positive_criteria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| KI9NqjLVDT | accept | accept_like | recovered_accept_high_precision | 2 | 2 | 0 | 2 | significance_contribution,empirical_adequacy |
| LebzzClHYw | accept | accept_like | recovered_accept_high_precision | 2 | 1 | 0 | 2 | novelty_originality,significance_contribution,empirical_adequacy |
| kam84eEmub | reject | borderline_positive | balanced_only_false_accept_risk | 4 | 1 | 0 | 3 | significance_contribution,clarity_reproducibility |
| ye3NrNrYOY | reject | borderline_positive | balanced_only_false_accept_risk | 3 | 2 | 0 | 3 | novelty_originality,significance_contribution |

## 逐案分析

### KI9NqjLVDT — recovered_accept_high_precision

- gold decision: `accept`
- calibrated label: `accept_like`
- strict binary: `accept`; lenient binary: `accept`
- support: real `2`, non-abstract `2`, empirical `0`, independent groups `2`, abstract-only `0`
- positive grounded criteria: `significance_contribution, empirical_adequacy`
- criterion statuses: novelty `missing`, significance `positive_grounded`, soundness `neutral_grounded`, empirical `positive_grounded`, clarity `missing`
- negative state: confirmed critical `0`, grounded major `0`, negative evidence `0`, stale gaps `3`, unsupported-with-strong `0`
- interpretation: 有真实 claim strong support、non-abstract support、独立 support group，并且 empirical adequacy 为 grounded positive；没有 grounded hard negative。

### LebzzClHYw — recovered_accept_high_precision

- gold decision: `accept`
- calibrated label: `accept_like`
- strict binary: `accept`; lenient binary: `accept`
- support: real `2`, non-abstract `1`, empirical `0`, independent groups `2`, abstract-only `1`
- positive grounded criteria: `novelty_originality, significance_contribution, empirical_adequacy`
- criterion statuses: novelty `positive_grounded`, significance `positive_grounded`, soundness `neutral_grounded`, empirical `positive_grounded`, clarity `missing`
- negative state: confirmed critical `0`, grounded major `0`, negative evidence `0`, stale gaps `3`, unsupported-with-strong `2`
- interpretation: 有真实 claim strong support、non-abstract support、独立 support group，并且 empirical adequacy 为 grounded positive；没有 grounded hard negative。

### kam84eEmub — balanced_only_false_accept_risk

- gold decision: `reject`
- calibrated label: `borderline_positive`
- strict binary: `reject`; lenient binary: `accept`
- support: real `4`, non-abstract `1`, empirical `0`, independent groups `3`, abstract-only `3`
- positive grounded criteria: `significance_contribution, clarity_reproducibility`
- criterion statuses: novelty `missing`, significance `positive_grounded`, soundness `missing`, empirical `neutral_ungrounded`, clarity `positive_grounded`
- negative state: confirmed critical `0`, grounded major `0`, negative evidence `0`, stale gaps `1`, unsupported-with-strong `0`
- interpretation: positive support/criterion 看似充足，但 empirical support 或 empirical grounded criterion 不足，因此 high-precision 拦截为 borderline，而不是 accept_like。

### ye3NrNrYOY — balanced_only_false_accept_risk

- gold decision: `reject`
- calibrated label: `borderline_positive`
- strict binary: `reject`; lenient binary: `accept`
- support: real `3`, non-abstract `2`, empirical `0`, independent groups `3`, abstract-only `1`
- positive grounded criteria: `novelty_originality, significance_contribution`
- criterion statuses: novelty `positive_grounded`, significance `positive_grounded`, soundness `neutral_grounded`, empirical `missing`, clarity `missing`
- negative state: confirmed critical `0`, grounded major `0`, negative evidence `0`, stale gaps `3`, unsupported-with-strong `0`
- interpretation: positive support/criterion 看似充足，但 empirical support 或 empirical grounded criterion 不足，因此 high-precision 拦截为 borderline，而不是 accept_like。

## 结论

1. `KI9NqjLVDT` 和 `LebzzClHYw` 说明 high-precision 规则可以恢复一部分 gold accept，且不会依赖单纯 strong-support-count。
2. `kam84eEmub` 和 `ye3NrNrYOY` 说明 balanced 规则会把局部正向 support 误读成 paper-level accept，主要缺口是 empirical support / empirical grounded criterion。
3. 因此正式推荐口径应保留三层：`accept_like`、`borderline_positive`、`not_assessable/reject_like`，不要把 borderline 直接当 accept。
4. 下一步如果继续优化，应优先改善 empirical evidence formation 和 hard-negative grounding，而不是继续调 accept/reject 阈值。
