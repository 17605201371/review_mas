# Final-View Flaw Lifecycle Simulation v1

## Decision Health

| metric | original | derived strict |
|---|---:|---:|
| `accuracy` | 0.7692 | 0.4615 |
| `accept_recall` | 0.0000 | 0.2222 |
| `reject_recall` | 1.0000 | 0.5333 |
| `macro_f1` | 0.4348 | 0.3819 |
| `predicted_accept_count` | 0 | 16 |

## Derived Label Counts

| label | count |
|---|---:|
| `accept_like` | 16 |
| `borderline` | 10 |
| `not_assessable` | 12 |
| `reject_like` | 1 |

## Recovered / False Accepts

- recovered_accept_ids: `['KI9NqjLVDT', 'jVEoydFOl9']`
- false_accept_ids: `['ye3NrNrYOY', 'uOrfve3prk', '9zEBK3E9bX', 'WpXq5n8yLb', 'NnExMNiTHw', 'a6SntIisgg', 'cklg91aPGk', 'QAgwFiIY4p', 'TPAj63ax4Y', 'xUe1YqEgd6', 'YXn76HMetm', 'KOUAayk5Kx', 'WLgbjzKJkk', 'LieTse3fQB']`

## 解释

这个 simulation 不是最终 decision rule。它验证的是：当 meta/excerpt/fallback artifact 不再作为强 reject blocker 时，系统是否能更诚实地区分 accept-like、reject-like、borderline 与 not-assessable。若 accept-like 仍然很少，说明 positive support formation 仍是瓶颈；若 not-assessable 很多，说明 final report 应明确暴露审稿上下文限制，而不是包装成论文缺陷。
