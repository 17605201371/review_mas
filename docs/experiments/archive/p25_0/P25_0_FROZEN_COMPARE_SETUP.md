# P25.0 Frozen Compare Setup

- frozen_commit: `876d795128180804add7ec557e27267ccf463b0f`
- compare_subset: `outputs/review_infer/p25_0_frozen_compare_subset.parquet`
- recovery_relevant_count: 8
- historical_sentinel_count: 2
- 4B model: `/reviewF/datasets/Qwen3___5-4B`
- 9B model: `/reviewF/datasets/Qwen3___5-9B`

## Frozen Parameters
- mode: s4
- max_turns: 8
- max_workers_per_turn: 3
- manager_batch_size: 2
- gpu_memory_utilization: 0.94
- max_num_seqs: 128
- max_model_len: 3072
- max_tokens: 640
- temperature: 0.2
- top_p: 0.95

## Freeze Rule
- manager policy, prompt, turn mode, validator, lifecycle and logging are held fixed.
- the only intended experimental variable is the model path: 4B vs 9B.

- runtime note: strict `gpu_memory_utilization=0.6` could not boot 9B on RTX 4090 24GB; both comparison runs were executed with shared `gpu_memory_utilization=0.94` while all other pipeline settings stayed fixed.
