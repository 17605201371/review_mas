# Final Recommendation Policy v2 Execution Result

## 结论

已按 clean 4B 审计结果执行 V2 推荐口径：不自动输出 `accept_like`，将 support-quality 正向样本标为 `borderline_positive`；只有 grounded major/critical flaw 标为 `reject_like`；证据不足或 targetless unresolved 较高标为 `not_assessable`。

## V2 View 分布

| view | count |
| --- | --- |
| accept_like | 0 |
| borderline_positive | 6 |
| borderline_insufficient | 12 |
| reject_like | 1 |
| not_assessable | 20 |

## 关键依据

| metric | value |
| --- | --- |
| real_strong_total | 28 |
| strong_method | 6 |
| strong_empirical_result | 11 |
| strong_table_or_figure | 10 |
| fallback_or_unbound_strong | 0 |

## 对比 Simulation

| rule | view_counts | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | {'reject_like': 39} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| support_quality | {'reject_like': 32, 'accept_like': 7} | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | uOrfve3prk, 9zEBK3E9bX, QAgwFiIY4p, TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw, BXY6fe7q31 |
| hard_negative_aware | {'not_assessable': 32, 'borderline': 6, 'reject_like': 1} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| combined_three_way | {'not_assessable': 32, 'accept_like': 4, 'reject_like': 1, 'borderline': 2} | 0.7179 | 0.4923 | 0.1111 | 0.9 | 4 | uOrfve3prk, 9zEBK3E9bX, TPAj63ax4Y | LebzzClHYw |

## 下一步

不要继续调 binary decision。下一步应人工核查 `borderline_positive` 与 false-accept-risk 样本，把它们写入论文 case study 或用于定义最终 9B confirmation subset。
