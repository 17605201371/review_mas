# Accept Support Failure Audit: Evidence JSON Contract v1 Fulltest39

## Aggregate

| group | rows | avg evidence turns | avg payload real strong | rows payload 2+ | avg final real strong | rows final 2+ | avg visible results | avg parse errors | avg unresolved | avg gaps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold_accept | 9 | 5.222 | 1.333 | 4 | 0.222 | 0 | 3.667 | 1.0 | 6.111 | 3.444 |
| gold_reject | 30 | 4.7 | 0.967 | 11 | 0.367 | 1 | 4.0 | 0.833 | 5.967 | 3.533 |

## 结论

在 JSON Contract v1 后，fallback 污染已明显下降，但 gold accept 样本仍未形成足够 payload/final real strong support。final-view hygiene 无法恢复 accept 的原因不是负面项没有清理，而是 accept-side positive evidence 仍不足。下一步应聚焦 accept 样本的正向证据形成：核心 claim 覆盖、method/result/table 证据转换、以及同一真实 claim 的独立支持形成。
