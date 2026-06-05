# Soft Evidence Recommendation v1 Decision

## 结论

v1 证明 recommendation 可以从硬约束转成软聚合，但当前 9B fulltest39 仍不支持把 recommendation 直接映射成二元 accept/reject。

## 分布

| soft_view_v1 | count |
| --- | --- |
| accept_like | 1 |
| borderline_insufficient | 12 |
| borderline_positive | 8 |
| not_assessable_evidence_conflict | 7 |
| not_assessable_uncertain | 4 |
| reject_like | 7 |

## 关键模拟

| mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict_accept_like_only | 0.7949 | 0.5412 | 0.1111 | 1.0 | 1 | 无 | jVEoydFOl9 |
| accept_or_borderline_positive_as_accept | 0.641 | 0.4944 | 0.2222 | 0.7667 | 9 | uOrfve3prk, NnExMNiTHw, cklg91aPGk, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, LieTse3fQB | BXY6fe7q31, jVEoydFOl9 |
| all_non_reject_as_accept_upper_bound | 0.3077 | 0.3059 | 0.7778 | 0.1667 | 32 | ye3NrNrYOY, uOrfve3prk, 7Dub7UXTXN, 9zEBK3E9bX, XyB4VvF01X, GE6iywJtsV, NnExMNiTHw, a6SntIisgg, cklg91aPGk, HPuLU6q7xq, fGXyvmWpw6, QAgwFiIY4p, TPAj63ax4Y, mHv6wcBb0z, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, ZHr0JajZfH, 9JRsAj3ymy, aTBE70xiFw, LieTse3fQB, kam84eEmub, N0isTh3rml, 2L7KQ4qbHi, aRxLDcxFcL | QAAsnSRwgu, X41c4uB4k0, KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9 |

## 解释

- `support_score` 已经能表达正向 evidence 强度，不再只看 support 数量。
- `negative_score` 和 `uncertainty_score` 作为软分进入推荐，不再由单条硬规则直接拦截。
- 但当把 `borderline_positive` 或 `accept_like` 映射为 accept 时，仍需重点看 false accept 风险。

## 下一步

不要继续硬调 final decision。若要进一步提高 accept recovery，应做 `Hard-Negative Extraction v1` 或 criterion assessment 的模型化标注，让系统产生更准确的 grounded negative/positive criterion，而不是继续改聚合阈值。
