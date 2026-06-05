# Evidence ID Collision Preservation v1 决策
## 实验目的
Retention v1 没有改善 `rows_with_2plus_real_strong_support` 后，补充审计发现 Evidence Agent 会在多轮里重复使用 `evidence-1` / `evidence-2` 表示不同证据。v1 尝试在 live state merge 前识别同名但内容不同的 evidence，并改写成新 id，避免新证据覆盖旧证据。
## mixed16 结果
| 版本 | final strong real | final non-abstract | final empirical | rows with 2+ final real strong | final collision-preserved items | predicted accept |
|---|---:|---:|---:|---:|---:|---:|
| isolation_v1_1 | 8 | 8 | 3 | 0 | 0 | 0 |
| retention_v1 | 8 | 8 | 3 | 0 | 0 | 0 |
| collision_v1 | 6 | 6 | 4 | 0 | 15 | 0 |

标准分析口径下，collision v1 的 `strong_support_on_real_claim` 为 `None`，低于 isolation/retention 的 `8`；`rows_with_2plus_real_strong_support` 仍为 `0`。
## 判断
不保留为 runtime 主线。v1 证明 collision 现象真实存在，final state 中确实出现了 15 条 `evidence_id_collision_preserved` evidence；但把 preservation 放入 live state 会改变后续轨迹，并没有提升正向证据形成，反而让 final strong real support 从 8 降到 6。
## 当前代码处理
保留 helper 和单元测试作为审计/后续离线重建基础，但通过 `ENABLE_EVIDENCE_ID_COLLISION_PRESERVATION = False` 禁用 live runtime 行为。这样不污染当前主线，同时保留对 collision 问题的可测能力。
## 下一步
不要继续把 collision preservation 直接塞进 live merge。下一步更合理的是做 **Evidence Payload Lineage / Offline Support Reconstruction v1**：从 turn logs 里重建 payload 级正向证据，离线判断如果不覆盖会不会恢复 2+ real support。只有离线证明有效，再考虑 final-view evidence view，而不是 live state mutation。
