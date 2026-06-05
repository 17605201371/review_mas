# Fallback Flaw Lifecycle Guard v1 Compare

## 指标表

| 指标 | Soft Focus v2 | Guard v1 | 变化 |
| --- | ---: | ---: | ---: |
| real strong support | 40 | 28 | -12 |
| method support total | 9 | 7 | -2 |
| trusted major/critical flaws | 8 | 13 | 5 |
| fallback/meta flaws | 38 | 35 | -3 |
| runtime false accept | 1 | 0 | -1 |
| high precision recovered accept | 1 | 0 | -1 |

## 解释

1. 这轮 guard 确认了安全性：runtime false accept 从 ``NnExMNiTHw`` 降为无。
2. 但正向 evidence/support 没有同步改善，strict accept-like 从 ``LebzzClHYw`` 降为无。
3. 当前的主要问题已经不是 fallback flaw 被误当论文缺陷这一单点，而是：真实 accept 仍被 unresolved / trusted hard-negative / method-soundness 缺口压住。

## 注意

real strong support 从 40 到 28 的下降不能直接解释为 guard 本身伤 evidence；本轮重新跑了 4B inference，存在轨迹波动。更可靠的结论是：guard 修复了 fallback flaw 语义，但仍不足以恢复 accept。
