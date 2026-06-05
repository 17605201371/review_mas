# Fallback Flaw Lifecycle Guard v1 Fulltest39 Confirmation

## 结论

这轮 4B fulltest39 确认 **Fallback Flaw Lifecycle Guard v1 应保留为运行时 bugfix**，但它不是 accept recall 的修复方案。

它解决的是一个明确工程错误：Critique/General Reviewer 的 fallback 或 malformed JSON 不能被当作论文的 major flaw / hard negative。确认结果显示，之前的 runtime false accept 被压下去了，但 runtime final decision 仍然是 health check 层面，不能作为论文主指标。

## 运行完整性

- 输入：`fallback_flaw_guard_v1_4b_fulltest39.jsonl`
- 样本数：39
- runtime final decision：39 reject / 0 accept
- gold accept：9
- gold reject：30

## 与 Soft Focus v2 的关键对比

| 指标 | Soft Focus v2 | Guard v1 confirmation | 解释 |
| --- | ---: | ---: | --- |
| runtime predicted accept | 1 | 0 | guard 后 runtime 不再误放 accept |
| runtime false accept | 1 | 0 | `NnExMNiTHw` 被压回 reject |
| runtime accept recall | 0.0 | 0.0 | accept 能力仍未恢复 |
| runtime reject recall | 0.9667 | 1.0 | reject safety 提升 |
| high-precision accept-like | 1 | 0 | strict 口径更保守，当前为 0 |
| high-precision false accept | 0 | 0 | 两轮都没有 strict false accept |
| three-way accept_like | 1 | 0 | 当前没有安全 accept_like |
| borderline_positive | 9 | 5 | 可疑正向样本减少 |
| not_assessable | 15 | 21 | 不可判定负担上升 |

## 具体样本信号

- `NnExMNiTHw`：Soft Focus v2 的 runtime false accept，本轮变为 reject。
- `ZHr0JajZfH`：上一轮 empirical structuring 中的典型 false accept，本轮变为 reject。
- `LebzzClHYw`：Soft Focus v2 strict accept-like 恢复样本，本轮不再满足 strict accept-like，说明 guard 后仍需补正向 method/soundness 或 unresolved cleanup。

## 判断

Guard v1 的价值是**清除系统 fallback/malformed critique 进入 hard-negative 的错误路径**。它提高了安全性，但没有解决真实 accept 恢复。下一步不能放松 decision threshold，而要继续审计 final-view hard-negative burden 和 method/soundness support 缺口。
