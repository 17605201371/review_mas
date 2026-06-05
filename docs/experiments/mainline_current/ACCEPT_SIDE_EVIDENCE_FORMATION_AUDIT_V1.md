# Accept-Side Evidence Formation Audit v1

本审计只读 fulltest39 的 turn payload 和 final ReviewState，不改 runtime、不重跑模型。目标是定位 gold accept 为什么没有形成真实 strong support。

## Accept vs Reject 对比

| group | rows | avg evidence turns | avg real strong | avg real medium | rows medium>=2 | rows strong>=2 | avg nonabs medium | avg broad turns | avg targeted high claims | avg unresolved | critique fallback avg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold_accept | 9 | 5.2222 | 0.3333 | 2.2222 | 6 | 0 | 0.0 | 4.7778 | 2.3333 | 5.6667 | 0.4444 |
| gold_reject | 30 | 4.2 | 0.7 | 2.1333 | 22 | 7 | 0.2333 | 3.1667 | 2.2 | 6.6333 | 0.4333 |

## Gold accept 失败模式分布

- `support_strength_calibration`: 6
- `broad_target_dominant`: 2
- `critique_fallback_interference`: 1

## 结论

当前 gold accept 的主问题不是 final decision 阈值。若 medium 支持主要来自 abstract，则不能直接升级为 strong；应先检查 Evidence context 是否真正包含非 abstract 的 method/result/table 片段，以及 broad target 是否让模型只抽取浅层自述。
