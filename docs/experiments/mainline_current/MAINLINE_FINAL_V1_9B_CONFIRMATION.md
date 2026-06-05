# Mainline-Final-v1 9B Confirmation

## 结论

这轮 9B 小确认有两个明确结论：

1. **9B 没有自然修复 final decision collapse。** 固定 8 条确认集仍然是 `8/8 reject`，accept recall 仍为 `0`。因此现在不应直接把下一次 9B fulltest 当正式主试验。
2. **9B 明显增强了 positive support formation。** 与同一子集 4B isolation 相比，`real_strong_support` 从 `2` 升到 `16`，`nonabstract_strong_support` 从 `2` 升到 `6`，`accept_rows_with_2plus_real_strong_support` 从 `0` 升到 `5`。这说明 9B 的价值不是 final label 自动变好，而是能给 final-view aggregation 提供更多可用正向证据。

所以当前下一刀不是继续调模型，也不是直接跑 9B fulltest，而是先做 `Criterion-Grounded Decision Simulation / Final Recommendation Policy v1`：把已有 real support、support quality、flaw lifecycle、criterion grounding 组合成可解释的 final-view recommendation。

## 配置

- model: `/reviewF/datasets/Qwen3___5-9B`
- subset: `mainline_final_v1_9b_confirmation_subset8.parquet`
- mode: `s4`
- max_turns: `8`
- max_workers_per_turn: `2`
- manager_batch_size: `2`
- max_model_len: `3072`
- max_tokens: `640`
- temperature/top_p: `0.2 / 0.95`
- max_num_seqs: `16`
- note: 当前运行入口不接受 `--seed`，实际 vLLM 日志显示 seed=0。

## Aggregate Metrics

| metric | 4B same subset | 9B confirmation |
|---|---:|---:|
| `row_count` | 8 | 8 |
| `predicted_accept_count` | 0 | 0 |
| `predicted_reject_count` | 8 | 8 |
| `accuracy` | 0.3750 | 0.3750 |
| `accept_recall` | 0.0000 | 0.0000 |
| `reject_recall` | 1.0000 | 1.0000 |
| `macro_f1` | 0.2727 | 0.2727 |
| `avg_reward` | 0.4014 | 0.3944 |
| `evidence_agent_calls` | 31 | 56 |
| `evidence_parse_errors` | 9 | 27 |
| `evidence_fallback_payloads` | 9 | 19 |
| `evidence_fallback_payload_rate` | 0.2903 | 0.3393 |
| `evidence_partial_json_recovery` | 2 | 0 |
| `strong_support_total` | 2 | 17 |
| `real_strong_support` | 2 | 16 |
| `nonabstract_strong_support` | 2 | 6 |
| `empirical_strong_support` | 1 | 0 |
| `fallback_strong_support` | 0 | 0 |
| `binding_precision` | 1.0000 | 0.9412 |
| `accept_rows_with_2plus_real_strong_support` | 0 | 5 |
| `patch_emitted_count` | 7 | 1 |
| `patch_validated_count` | 7 | 1 |
| `patch_committed_count` | 0 | 0 |
| `model_generated_commit_count` | 0 | 0 |
| `system_salvaged_commit_count` | 0 | 0 |
| `unresolved_count` | 50 | 62 |
| `evidence_gap_count` | 27 | 20 |
| `flaw_count` | 8 | 0 |

## 判断

- `Go to 9B fulltest`：暂不建议。原因不是 9B 没有价值，而是 final decision / recommendation policy 尚未能利用 9B 形成的正向证据。
- `Keep 9B as candidate main model`：建议保留。9B 在 support formation 上有明显正向信号。
- `Next cut`：先做离线 criterion-grounded decision aggregation，验证在不改 runtime、不重跑模型的情况下，是否能把 9B/4B 形成的 support 转成更合理的 accept-like / reject-like / borderline recommendation。
