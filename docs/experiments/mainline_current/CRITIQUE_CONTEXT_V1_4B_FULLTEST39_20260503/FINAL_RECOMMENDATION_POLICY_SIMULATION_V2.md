# Final Recommendation Policy Simulation V2

## 结论

单纯 support-quality 规则会产生 accept，但必须结合 hard-negative / unresolved lifecycle 才能避免把正向 evidence 误当充分接收条件。当前最稳妥的正式口径仍是多类 recommendation view：`accept_like / borderline / reject_like / not_assessable`；runtime binary accept/reject 不作为主指标。

## Simulation

| rule | view_counts | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | {'reject_like': 39} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| support_quality | {'accept_like': 14, 'reject_like': 25} | 0.5128 | 0.4142 | 0.2222 | 0.6 | 14 | ye3NrNrYOY, uOrfve3prk, 7Dub7UXTXN, 9zEBK3E9bX, GE6iywJtsV, WpXq5n8yLb, NnExMNiTHw, cklg91aPGk, QAgwFiIY4p, YXn76HMetm, WLgbjzKJkk, aTBE70xiFw | QAAsnSRwgu, BXY6fe7q31 |
| hard_negative_aware | {'borderline': 13, 'not_assessable': 24, 'reject_like': 2} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| combined_three_way | {'borderline': 6, 'not_assessable': 24, 'accept_like': 7, 'reject_like': 2} | 0.5897 | 0.371 | 0.0 | 0.7667 | 7 | uOrfve3prk, 7Dub7UXTXN, 9zEBK3E9bX, cklg91aPGk, QAgwFiIY4p, YXn76HMetm, WLgbjzKJkk | 无 |

## 下一步

保留 clean 4B dry-run baseline；正式主试验前把 final recommendation 固定为 final-view 派生口径，不改 live state，不回 controller。
