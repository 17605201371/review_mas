# Evidence Support Strength Calibration v1 Simulation

本模拟只读 `accept_side_evidence_formation_audit_v1.json`，不改 runtime、不重跑模型。目标是验证“把 medium support 当 strong”是否安全。

| simulation | predicted_accept | accuracy | macro_f1 | accept_recall | reject_recall | recovered_accept | false_accept |
|---|---:|---:|---:|---:|---:|---|---|
| all_real_medium_or_strong_2plus | 27 | 0.3846 | 0.381 | 0.6667 | 0.3 | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT, LebzzClHYw, X41c4uB4k0, hj323oR3rw | 7Dub7UXTXN, 9JRsAj3ymy, HPuLU6q7xq, KOUAayk5Kx, LieTse3fQB, N0isTh3rml, QAgwFiIY4p, TPAj63ax4Y, WLgbjzKJkk, WNxlJJIEVj, WpXq5n8yLb, XH3OiIhtvf, XyB4VvF01X, ZHr0JajZfH, aRxLDcxFcL, cklg91aPGk, kam84eEmub, mHv6wcBb0z, uOrfve3prk, xUe1YqEgd6, ye3NrNrYOY |
| nonabstract_medium_or_strong_1plus | 14 | 0.5641 | 0.4759 | 0.3333 | 0.6333 | 1HCN4pjTb4, LebzzClHYw, hj323oR3rw | 9JRsAj3ymy, HPuLU6q7xq, NnExMNiTHw, QAgwFiIY4p, TPAj63ax4Y, ZHr0JajZfH, aRxLDcxFcL, cklg91aPGk, mHv6wcBb0z, uOrfve3prk, xUe1YqEgd6 |
| empirical_medium_or_strong_1plus | 6 | 0.6667 | 0.4635 | 0.1111 | 0.8333 | 1HCN4pjTb4 | NnExMNiTHw, TPAj63ax4Y, aRxLDcxFcL, cklg91aPGk, mHv6wcBb0z |
| medium_2plus_low_unresolved | 15 | 0.4872 | 0.3981 | 0.2222 | 0.5667 | 1HCN4pjTb4, hj323oR3rw | 7Dub7UXTXN, 9JRsAj3ymy, LieTse3fQB, N0isTh3rml, QAgwFiIY4p, WLgbjzKJkk, XH3OiIhtvf, XyB4VvF01X, ZHr0JajZfH, cklg91aPGk, mHv6wcBb0z, uOrfve3prk, xUe1YqEgd6 |

## 结论

naive 的 medium->strong 会恢复部分 accept，但 false accept 同时明显增加；non-abstract/empirical 版本更安全但召回很低。这说明下一刀不应直接把 medium 升 strong，而应让 Evidence Agent 在 accept 样本上形成更多 non-abstract / result / table grounded support。
