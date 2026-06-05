# Final Recommendation Policy Simulation V2

## 结论

单纯 support-quality 规则会产生 accept，但必须结合 hard-negative / unresolved lifecycle 才能避免把正向 evidence 误当充分接收条件。当前最稳妥的正式口径仍是多类 recommendation view：`accept_like / borderline / reject_like / not_assessable`；runtime binary accept/reject 不作为主指标。

## Simulation

| rule | view_counts | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | {'reject_like': 39} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| support_quality | {'accept_like': 9, 'reject_like': 30} | 0.5897 | 0.4222 | 0.1111 | 0.7333 | 9 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, cklg91aPGk, QAgwFiIY4p, YXn76HMetm, aTBE70xiFw | QAAsnSRwgu |
| hard_negative_aware | {'borderline': 8, 'not_assessable': 28, 'reject_like': 3} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| combined_three_way | {'borderline': 3, 'not_assessable': 28, 'accept_like': 5, 'reject_like': 3} | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | uOrfve3prk, 9zEBK3E9bX, cklg91aPGk, QAgwFiIY4p | QAAsnSRwgu |

## 下一步

保留 clean 4B dry-run baseline；正式主试验前把 final recommendation 固定为 final-view 派生口径，不改 live state，不回 controller。
