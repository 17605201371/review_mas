# Final Recommendation Policy v4 Simulation

| mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict_accept_like_only | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| borderline_positive_as_accept | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| context_limited_as_accept_risk | 0.4872 | 0.3981 | 0.2222 | 0.5667 | 15 | ye3NrNrYOY, uOrfve3prk, 9zEBK3E9bX, WpXq5n8yLb, NnExMNiTHw, cklg91aPGk, QAgwFiIY4p, TPAj63ax4Y, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, WLgbjzKJkk, LieTse3fQB | KI9NqjLVDT, jVEoydFOl9 |
| targetless_unresolved_as_accept_risk | 0.6154 | 0.5375 | 0.4444 | 0.6667 | 14 | 7Dub7UXTXN, HPuLU6q7xq, fGXyvmWpw6, ZHr0JajZfH, 9JRsAj3ymy, aTBE70xiFw, kam84eEmub, N0isTh3rml, 2L7KQ4qbHi, aRxLDcxFcL | hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, 1HCN4pjTb4 |
| unverified_hard_negative_as_accept_risk | 0.7692 | 0.5846 | 0.2222 | 0.9333 | 4 | GE6iywJtsV, mHv6wcBb0z | LebzzClHYw, BXY6fe7q31 |
| all_non_reject_as_accept_upper_bound | 0.3333 | 0.3294 | 0.8889 | 0.1667 | 33 | ye3NrNrYOY, uOrfve3prk, 7Dub7UXTXN, 9zEBK3E9bX, GE6iywJtsV, WpXq5n8yLb, NnExMNiTHw, cklg91aPGk, HPuLU6q7xq, fGXyvmWpw6, QAgwFiIY4p, TPAj63ax4Y, mHv6wcBb0z, xUe1YqEgd6, YXn76HMetm, KOUAayk5Kx, ZHr0JajZfH, WLgbjzKJkk, 9JRsAj3ymy, aTBE70xiFw, LieTse3fQB, kam84eEmub, N0isTh3rml, 2L7KQ4qbHi, aRxLDcxFcL | hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9 |
