# Mainline-Final-v1 Unified Results Table

## 总结

这份表汇总当前 `Mainline-Final-v1` 预跑结果。它不是正式二分类主实验结论，而是论文主线收口表：runtime final decision 作为 health check，final-view recommendation 作为更可信的诊断输出。

## Runtime Health

| metric | value |
| --- | ---: |
| rows | 39 |
| gold_accept | 9 |
| gold_reject | 30 |
| runtime_accept | 0 |
| runtime_reject | 39 |
| avg_reward | 0.4674 |

## Evidence / Support State

| metric | value |
| --- | ---: |
| real_strong_support_total | 37 |
| non_abstract_support_total | 18 |
| empirical_support_total | 5 |
| raw_fallback_strong_support_excluded | 13 |
| rows_with_2plus_real_strong | 14 |
| rows_with_2plus_nonabstract | 5 |

说明：`raw_fallback_strong_support_excluded` 是 raw ReviewState 中的 fallback-bound strong support 残留，只作为污染诊断指标；final-view recommendation 不把它计入 decision-eligible support。

## Criterion Sim4 Combined Rule

| metric | value |
| --- | ---: |
| predicted_accept_count | 10 |
| recovered_accept_count | 3 |
| false_accept_count | 7 |
| accept_recall | 0.3333 |
| reject_recall | 0.7667 |
| macro_f1 | 0.5477 |

## Negative Anchor Confirmation

| metric | value |
| --- | ---: |
| false_accept_trusted_blocker_rows | 0 |
| recovered_accept_trusted_blocker_rows | 1 |
| parse_error_rows_total | 0 |

## Support Quality Filters

| metric | value |
| --- | ---: |
| two_positive_pred_accept | 4 |
| two_positive_true_accept | 2 |
| two_positive_false_accept | 2 |
| high_precision_pred_accept | 1 |
| high_precision_true_accept | 1 |
| high_precision_false_accept | 0 |

## Final Recommendation View

| metric | value |
| --- | ---: |
| accept_like | 1 |
| borderline_positive | 12 |
| borderline_insufficient | 3 |
| reject_like | 1 |
| not_assessable | 22 |

## 当前决策

- 不继续调 runtime accept/reject 阈值。
- 不继续 sticky/throttle/progression gate。
- 不继续强造 negative blocker。
- 下一阶段应将 `Final Recommendation View v1` 纳入论文主表和 final report 展示层。
