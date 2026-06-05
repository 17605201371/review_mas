# Empirical Evidence Sufficiency Audit v1

## 结论

gold accept 样本 `9` 条，其中 high-precision 恢复 `2` 条。未恢复样本主要不是 final aggregation 阈值问题，而是 empirical/result/table/ablation support 仍不足，或 empirical criterion 没有 grounded positive。

## Accept-side case table

| paper_id | calibrated | audit_label | real | nonabs | empirical_support | empirical_criterion_grounded | state_empirical_evidence | unresolved_empirical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1HCN4pjTb4 | reject_like | false_reject_negative_burden_or_quality_filter | 3 | 1 | 0 | False | 2 | 2 |
| BXY6fe7q31 | borderline_positive | other | 2 | 1 | 0 | False | 1 | 3 |
| KI9NqjLVDT | accept_like | recovered_accept_with_empirical_or_grounded_empirical | 2 | 2 | 0 | True | 1 | 8 |
| LebzzClHYw | accept_like | recovered_accept_with_empirical_or_grounded_empirical | 2 | 1 | 0 | True | 1 | 3 |
| QAAsnSRwgu | not_assessable | false_reject_no_real_support | 0 | 0 | 0 | False | 0 | 0 |
| X41c4uB4k0 | not_assessable | false_reject_no_real_support | 0 | 0 | 0 | False | 2 | 3 |
| gzqrANCF4g | not_assessable | false_reject_no_real_support | 0 | 0 | 0 | False | 2 | 3 |
| hj323oR3rw | not_assessable | false_reject_no_real_support | 0 | 0 | 0 | False | 0 | 1 |
| jVEoydFOl9 | borderline_insufficient | false_reject_negative_burden_or_quality_filter | 2 | 0 | 0 | False | 1 | 1 |

## 解释

- `calibrated_high_precision` 要求 empirical support 或 grounded empirical adequacy，是为了防止把局部 claim support 误当成 paper-level accept。
- high-precision 召回低，说明下一步如果要继续提高 accept recall，应优先改善 empirical evidence formation，而不是继续放松 recommendation 规则。
