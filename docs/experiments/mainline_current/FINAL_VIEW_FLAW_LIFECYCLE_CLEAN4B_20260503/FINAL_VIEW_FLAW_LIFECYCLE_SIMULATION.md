# Final-View Flaw Lifecycle Simulation v1

## Decision Health

| metric | original | derived strict |
|---|---:|---:|
| `accuracy` | 0.7692 | 0.7179 |
| `accept_recall` | 0.0000 | 0.2222 |
| `reject_recall` | 1.0000 | 0.8667 |
| `macro_f1` | 0.4348 | 0.5460 |
| `predicted_accept_count` | 0 | 6 |

## Derived Label Counts

| label | count |
|---|---:|
| `not_assessable` | 7 |
| `borderline` | 20 |
| `accept_like` | 6 |
| `reject_like` | 6 |

## Recovered / False Accepts

- recovered_accept_ids: `['LebzzClHYw', 'BXY6fe7q31']`
- false_accept_ids: `['uOrfve3prk', '9zEBK3E9bX', 'TPAj63ax4Y', 'ZHr0JajZfH']`

## 解释

这个 simulation 不是最终 decision rule。它验证的是：当 meta/excerpt/fallback artifact 不再作为强 reject blocker 时，系统是否能更诚实地区分 accept-like、reject-like、borderline 与 not-assessable。若 accept-like 仍然很少，说明 positive support formation 仍是瓶颈；若 not-assessable 很多，说明 final report 应明确暴露审稿上下文限制，而不是包装成论文缺陷。
