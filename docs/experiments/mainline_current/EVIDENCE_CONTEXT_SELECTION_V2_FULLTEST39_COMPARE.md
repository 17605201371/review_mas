# Evidence Context Selection v2 Fulltest39 Compare

本比较使用 4B fulltest39，同口径对比 clean baseline 与 Evidence Context Selection v2。结论用中文记录；本轮只改 Evidence Agent context selection，不改 decision/controller。

| metric | clean baseline | context v2 | delta |
|---|---:|---:|---:|
| `predicted_accept_count` | 0 | 0 | 0.0 |
| `accept_recall` | 0.0 | 0.0 | 0.0 |
| `reject_recall` | 1.0 | 1.0 | 0.0 |
| `macro_f1` | 0.4347826086956522 | 0.4347826086956522 | 0.0 |
| `real_strong_support_total` | 21 | 27 | 6.0 |
| `nonabstract_strong_support_total` | 19 | 24 | 5.0 |
| `empirical_strong_support_total` | 17 | 18 | 1.0 |
| `fallback_strong_support_total` | 0 | 0 | 0.0 |
| `rows_with_2plus_real_strong_support` | 6 | 7 | 1.0 |
| `accept_rows_with_2plus_real_strong_support` | 0 | 2 | 2.0 |
| `evidence_json_invalid_or_missing_count` | 18 | 9 | -9.0 |
| `evidence_json_fallback_used_count` | 1 | 0 | -1.0 |
| `unresolved_count` | 251 | 226 | -25.0 |
| `evidence_gap_count` | 165 | 156 | -9.0 |
| `patch_committed_count` | 4 | 3 | -1.0 |
| `rows_with_any_commit` | 4 | 3 | -1.0 |
| `legacy_controller_active_turns` | 0 | 0 | 0.0 |
| `broad_target_turn_rate` | 0.9061032863849765 | 0.9560975609756097 | 0.05 |

## 结论

- `Evidence Context Selection v2` 应保留为候选主线改动：它在旧 controller 关闭的前提下提升了 real / non-abstract support，并且没有引入 fallback strong 或 false accept。
- 这轮没有解决 final decision：predicted accept 仍为 0，说明 final recommendation policy 仍不能作为主指标，只能作为 health check。
- 主要剩余瓶颈是 broad target 与 accept-side evidence focus：v2 改善了 context 可见性，但 broad target rate 仍高，Evidence Agent 仍容易在多个 claim 间分散。
