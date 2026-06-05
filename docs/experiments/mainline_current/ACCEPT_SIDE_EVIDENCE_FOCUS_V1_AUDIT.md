# Accept-Side Evidence Formation Audit v1

本审计只读 fulltest39 的 turn payload 和 final ReviewState，不改 runtime、不重跑模型。目标是定位 gold accept 为什么没有形成真实 strong support。

## Accept vs Reject 对比

| group | rows | avg evidence turns | avg real strong | avg real medium | rows medium>=2 | rows strong>=2 | avg nonabs medium | avg broad turns | avg targeted high claims | avg unresolved | critique fallback avg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold_accept | 9 | 3.4444 | 1.2222 | 1.8889 | 5 | 4 | 0.0 | 2.2222 | 2.2222 | 5.0 | 0.4444 |
| gold_reject | 30 | 3.7667 | 0.6 | 2.2 | 21 | 5 | 0.2 | 2.8667 | 1.7667 | 6.2667 | 0.4667 |

## Gold accept 失败模式分布

- `support_strength_calibration`: 4
- `critique_fallback_interference`: 2
- `negative_burden_after_evidence`: 2
- `broad_target_dominant`: 1

## 结论

当前 gold accept 的主问题不是 final decision 阈值。若 medium 支持主要来自 abstract，则不能直接升级为 strong；应先检查 Evidence context 是否真正包含非 abstract 的 method/result/table 片段，以及 broad target 是否让模型只抽取浅层自述。
