# Final Recommendation Policy v2 Execution Result

## 结论

已按当前 fulltest39 审计结果执行 V2 推荐口径：不自动输出 `accept_like`，将 support-quality 正向样本标为 `borderline_positive`；只有 grounded major/critical flaw 标为 `reject_like`；证据不足或 targetless unresolved 较高标为 `not_assessable`。

## V2 View 分布

| view | count |
| --- | --- |
| accept_like | 0 |
| borderline_positive | 15 |
| borderline_insufficient | 2 |
| reject_like | 1 |
| not_assessable | 21 |

## 关键依据

| metric | value |
| --- | --- |
| real_strong_total | 49 |
| strong_method | 13 |
| strong_empirical_result | 35 |
| strong_table_or_figure | 0 |
| fallback_or_unbound_strong | 0 |

## 对比 Simulation

| rule | view_counts | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | {} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| sim_a_abstract_only_excluded | {} | 0.4615 | 0.3819 | 0.2222 | 0.5333 | 16 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, cklg91aPGk, QAgwFiIY4p, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, LieTse3fQB | KI9NqjLVDT, jVEoydFOl9 |
| sim_b_non_abstract_support_ge1 | {} | 0.4615 | 0.3819 | 0.2222 | 0.5333 | 16 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, cklg91aPGk, QAgwFiIY4p, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, LieTse3fQB | KI9NqjLVDT, jVEoydFOl9 |
| sim_c_independent_groups_ge2 | {} | 0.4615 | 0.3819 | 0.2222 | 0.5333 | 16 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, cklg91aPGk, QAgwFiIY4p, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, LieTse3fQB | KI9NqjLVDT, jVEoydFOl9 |
| sim_d_empirical_support_for_empirical_claims | {} | 0.4872 | 0.3981 | 0.2222 | 0.5667 | 15 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, cklg91aPGk, QAgwFiIY4p, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, LieTse3fQB | KI9NqjLVDT, jVEoydFOl9 |
| sim_e_method_plus_result_combination | {} | 0.6667 | 0.4635 | 0.1111 | 0.8333 | 6 | ye3NrNrYOY, uOrfve3prk, QAgwFiIY4p, xUe1YqEgd6, WLgbjzKJkk | jVEoydFOl9 |
| sim_f_criterion_grounded_accept_signal | {} | 0.3846 | 0.3743 | 0.5556 | 0.3333 | 25 | ye3NrNrYOY, uOrfve3prk, 7Dub7UXTXN, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, cklg91aPGk, fGXyvmWpw6, QAgwFiIY4p, TPAj63ax4Y, mHv6wcBb0z, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, aTBE70xiFw, LieTse3fQB, N0isTh3rml, aRxLDcxFcL | QAAsnSRwgu, X41c4uB4k0, KI9NqjLVDT, BXY6fe7q31, jVEoydFOl9 |

## 下一步

不要继续调 binary decision。下一步应人工核查 `borderline_positive` 与 false-accept-risk 样本，把它们写入论文 case study 或用于定义最终 9B confirmation subset。
