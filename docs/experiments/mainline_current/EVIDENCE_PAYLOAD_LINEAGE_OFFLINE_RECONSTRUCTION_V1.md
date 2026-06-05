# Evidence Payload Lineage / Offline Reconstruction v1

本报告只做离线审计，不改变 runtime、不重跑模型。目标是比较 Evidence Agent payload 层已经形成的 real strong support 与 final ReviewState 实际保留下来的 support。

| dataset | rows | payload real strong | final real strong | payload non-abstract | final non-abstract | payload empirical | final empirical | rows payload 2+ | rows final 2+ | duplicate payload ids |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| isolation_v1_1_mixed16 | 16 | 23 | 8 | 20 | 8 | 11 | 3 | 6 | 0 | 37 |
| isolation_v1_1_fulltest39 | 39 | 33 | 9 | 19 | 9 | 9 | 5 | 10 | 0 | 56 |

## 结论

payload 层已经存在明显更多 real strong support，且多个样本在 payload 层达到 2+，但 final state 中 2+ 样本仍为 0。下一步不应继续调 final decision 阈值，而应优先做 final-view evidence lineage / support reconstruction，或至少在论文中明确报告 payload-to-state support loss。
