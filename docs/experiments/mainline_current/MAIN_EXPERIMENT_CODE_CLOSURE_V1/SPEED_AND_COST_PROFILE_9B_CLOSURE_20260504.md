# SPEED_AND_COST_PROFILE_9B_CLOSURE_20260504

## 结论

这是最新 9B fulltest39 closure run 的速度/成本 profile。它不改变 runtime，只用于正式主试验前估算扩样成本。

| metric | value |
| --- | ---: |
| row_count | 39 |
| run_minutes_from_log | 75.75 |
| seconds_per_paper_from_log | 116.54 |
| avg_turns_per_paper | 6.15 |
| median_turns_per_paper | 7 |
| max_turns_hit_rows | 14 |
| manager_turns | 240 |
| selected_worker_calls | 311 |
| approx_model_calls_including_manager | 551 |
| approx_model_calls_per_paper | 14.13 |
| prompt_call_count_from_log | 0 |
| avg_prompt_seconds | None |
| avg_input_toks_per_sec | None |
| avg_output_toks_per_sec | None |

## 解释

- wall-clock 约 `75.75` 分钟，包含模型加载、compile/cache、推理和 shutdown。
- 平均每篇约 `116.54` 秒；如果扩到 1000 篇 9B 单卡串行，粗略会非常慢，因此正式大规模主试验应先做 pilot / 分层抽样，或用 4B 跑大样本、9B 跑确认集。
- `max_turns_hit_rows=14`，说明 turn budget 对一部分样本仍可能是瓶颈。
- 当前速度 profile 足够支持 39 条 fulltest / 小确认，不建议直接开 1w 级 9B 全量。
