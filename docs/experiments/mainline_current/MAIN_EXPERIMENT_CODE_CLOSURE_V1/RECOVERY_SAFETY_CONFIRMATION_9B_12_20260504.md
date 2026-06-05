# Recovery Safety Confirmation 9B-12 20260504

## 结论

这次确认集使用当前代码和 locked gold labels 跑 9B 前 12 条 fulltest39 样本，目的是验证 recovery safety 改动没有破坏主线。

结论：**通过小确认**。在这 12 条上，support formation 没有下降，JSON/fallback 没有恶化，旧 controller 没有回潮，recovery safety 没有引入异常 commit。

## 运行口径

- model：`/reviewF/datasets/Qwen3___5-9B`
- dataset：`/reviewF/datasets/drmas_review/test.parquet`
- split：`test`
- limit：`12`
- mode：`s4`
- max_turns：`8`
- gold labels：`docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json`
- output：`outputs/results_main/review_infer/recovery_safety_confirm_9b_12_20260504_gold.jsonl`

样本：`ye3NrNrYOY, WNxlJJIEVj, uOrfve3prk, hj323oR3rw, 7Dub7UXTXN, 9zEBK3E9bX, XyB4VvF01X, GE6iywJtsV, QAAsnSRwgu, WpXq5n8yLb, X41c4uB4k0, NnExMNiTHw`

## 对比结果

基线是最新 9B closure fulltest39 中同一批前 12 条样本；确认集是当前代码重跑结果。

| metric | baseline first12 | confirmation |
| --- | ---: | ---: |
| `accuracy` | 0.75 | 0.75 |
| `accept_recall` | 0.0 | 0.0 |
| `reject_recall` | 1.0 | 1.0 |
| `macro_f1` | 0.42857142857142855 | 0.42857142857142855 |
| `predicted_accept_count` | 0 | 0 |
| `real_strong_support_total` | 17 | 19 |
| `nonabstract_strong_support_total` | 17 | 19 |
| `empirical_strong_support_total` | 7 | 7 |
| `method_strong_support_total` | 4 | 6 |
| `table_or_figure_strong_support_total` | 7 | 7 |
| `independent_support_group_total` | 14 | 16 |
| `fallback_strong_support_total` | 0 | 0 |
| `evidence_fallback_payloads` | 0 | 0 |
| `evidence_json_invalid_or_missing_count` | 0 | 0 |
| `patch_emitted_count` | 28 | 28 |
| `patch_committed_count` | 0 | 0 |
| `rows_with_any_commit` | 0 | 0 |
| `unresolved_count` | 76 | 77 |
| `evidence_gap_count` | 36 | 36 |
| `flaw_count` | 14 | 14 |
| `legacy_controller_active_turns` | 0 | 0 |

## Recovery safety 观察

failure codes：`{'BLOCKED_BY_POLICY': 24, 'INSUFFICIENT_EVIDENCE': 4}`

- `patch_emitted_count`：28 -> 28，没有下降。
- `patch_committed_count`：0 -> 0，仍为 0，说明这轮没有因为 safety 改动产生新 commit，也没有放松 validator。
- `fallback_strong_support_total`：0 -> 0，仍为 0。
- `legacy_controller_active_turns`：0 -> 0，旧 controller 没有回潮。

## Go / No-Go

- 对小确认集：Go。
- 对正式主试验：仍建议先把 locked label、support quality、criterion grounding、recovery safety 和统一分析脚本作为封版口径；如果要把当前代码作为正式 9B 主试验 baseline，可直接做封版 fulltest39 rerun。

## 注意

这不是性能提升实验，也不是新的 controller 实验。它只验证 recovery safety 改动在小确认集上没有明显副作用。
