# Evidence Context Selection v2 Decision

## 结论

保留为候选主线改动。

## 依据

相对 clean baseline，v2 在关闭旧 controller 的前提下带来以下变化：

- `real_strong_support_total`: 21 -> 27
- `nonabstract_strong_support_total`: 19 -> 24
- `empirical_strong_support_total`: 17 -> 18
- `accept_rows_with_2plus_real_strong_support`: 0 -> 2
- `evidence_json_invalid_or_missing_count`: 18 -> 9
- `evidence_json_fallback_used_count`: 1 -> 0
- `unresolved_count`: 251 -> 226
- `fallback_strong_support_total`: 0 -> 0
- `legacy_controller_active_turns`: 0 -> 0

这说明 v2 修复了 v1 context selection 的一个真实问题：之前很多 `results/table` 可见性其实来自 abstract 词命中；v2 更倾向真实 section header 后，positive support 和 JSON 稳定性都有改善。

## 未解决问题

- final decision 仍然是 39 条全 reject，accept recall 仍为 0。
- `broad_target_turn_rate` 仍高，并从 0.906 上升到 0.956。
- patch commit 略降：`patch_committed_count` 4 -> 3。

因此 v2 不是 final decision 修复，也不是主试验终版。它只是 evidence-side 输入修复。

## 下一步

下一步不应调 accept/reject 阈值，也不应恢复 sticky/throttle/gate。建议做：

`Accept-Side Evidence Focus v1`

目标是在 Evidence Agent 内部减少 broad target 对 accept-side support formation 的稀释，让每个 evidence turn 更集中地围绕 1–2 个高重要真实 claim 寻找 method/result/table support。该改动仍应保持小规模、可回退，并继续不改变 final decision policy。
