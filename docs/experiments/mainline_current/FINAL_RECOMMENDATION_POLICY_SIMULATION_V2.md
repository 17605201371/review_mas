# Final Recommendation Policy Simulation V2

## 结论

单纯 support-quality 规则会产生 accept，但必须结合 hard-negative / unresolved lifecycle 才能避免把正向 evidence 误当充分接收条件。当前最稳妥的正式口径仍是多类 recommendation view：`accept_like / borderline / reject_like / not_assessable`；runtime binary accept/reject 不作为主指标。

## Simulation

| rule | view_counts | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | {'reject_like': 39} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| support_quality | {'reject_like': 32, 'accept_like': 7} | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | uOrfve3prk, 9zEBK3E9bX, QAgwFiIY4p, TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw, BXY6fe7q31 |
| hard_negative_aware | {'not_assessable': 32, 'borderline': 6, 'reject_like': 1} | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| combined_three_way | {'not_assessable': 32, 'accept_like': 4, 'reject_like': 1, 'borderline': 2} | 0.7179 | 0.4923 | 0.1111 | 0.9 | 4 | uOrfve3prk, 9zEBK3E9bX, TPAj63ax4Y | LebzzClHYw |

## 下一步

保留 clean 4B dry-run baseline；正式主试验前把 final recommendation 固定为 final-view 派生口径，不改 live state，不回 controller。
