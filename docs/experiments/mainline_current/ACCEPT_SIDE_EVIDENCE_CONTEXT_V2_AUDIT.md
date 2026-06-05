# Accept-Side Evidence Formation Audit v1

本审计只读 fulltest39 的 turn payload 和 final ReviewState，不改 runtime、不重跑模型。目标是定位 gold accept 为什么没有形成真实 strong support。

## Accept vs Reject 对比

| group | rows | avg evidence turns | avg real strong | avg real medium | rows medium>=2 | rows strong>=2 | avg nonabs medium | avg broad turns | avg targeted high claims | avg unresolved | critique fallback avg |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gold_accept | 9 | 4.7778 | 0.7778 | 1.4444 | 3 | 2 | 0.0 | 3.7778 | 2.3333 | 4.5556 | 0.8889 |
| gold_reject | 30 | 4.1 | 0.9 | 1.7 | 15 | 5 | 0.2333 | 3.1 | 1.8 | 6.1667 | 0.3667 |

## Gold accept 失败模式分布

- `support_strength_calibration`: 2
- `critique_fallback_interference`: 6
- `broad_target_dominant`: 1

## 结论

当前 gold accept 的主问题不是 final decision 阈值。若 medium 支持主要来自 abstract，则不能直接升级为 strong；应先检查 Evidence context 是否真正包含非 abstract 的 method/result/table 片段，以及 broad target 是否让模型只抽取浅层自述。
