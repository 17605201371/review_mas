# Accept Support Failure Audit v1

本审计只读已有 fulltest39 jsonl，不改 runtime、不重跑模型。目标是解释 gold accept 为什么在 payload lineage 层仍缺少足够 real strong support。

## Accept vs Reject aggregate

| group | rows | avg evidence turns | avg payload real strong | rows payload 2+ | avg final real strong | rows final 2+ | avg visible results turns | avg broad target turns | avg unresolved | avg evidence gaps |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold_accept | 9 | 4.2222 | 0.1111 | 0 | 0.0 | 0 | 3.1111 | 2.8889 | 6.7778 | 3.0 |
| gold_reject | 30 | 4.7 | 1.0667 | 10 | 0.3 | 0 | 3.8 | 3.8333 | 4.9667 | 3.8667 |

## 结论

如果 gold accept 在 payload 层也缺少 2+ real strong support，那么瓶颈不是 final decision，而是 accept-side evidence formation：Evidence Agent 虽然能看到 method/results/table，但没有把这些上下文稳定转成支持 gold-accept 论文的真实 claim evidence。
