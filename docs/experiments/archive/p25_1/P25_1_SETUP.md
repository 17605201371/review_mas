# P25.1 Setup

- frozen_commit: `26320952a83fc0e51a1de0d924acf5db418ad4f9`
- 9B main subset: `outputs/review_infer/p25_1_9b_expanded_subset.parquet`
- 4B reference subset: `outputs/review_infer/p25_1_4b_reference_subset.parquet`
- expanded recovery_relevant_count: 24
- fixed 4B reference_count: 8
- historical_sentinel_count: 2
- 4B model: `/reviewF/datasets/Qwen3___5-4B`
- 9B model: `/reviewF/datasets/Qwen3___5-9B`

## Selection Rule
- Expanded recovery-relevant set keeps the 8 carry-over p25.0 rows for continuity, then adds 16 pilot2 rows with the strongest pre-recovery signals from frozen S4 logs: recovery-oriented action turns, conflict turns, downgrade/retract evidence, and revision events. Historical sentinel rows remain separate and are not counted inside the 24-row expanded recovery-relevant total.

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

## Runtime Note
- Original strict-frozen startup at gpu_memory_utilization=0.6 could not boot 9B on RTX 4090 24GB; the p25.1 bounded runs keep all pipeline settings fixed and share gpu_memory_utilization=0.94.

## Fixed 4B Reference IDs
- 2Cg4YrsCMA, NhLBhx5BVY, 9EBSEkFSje, GSckuQMzBG, IqaQZ1Jdky, kdriw2a8sl, qgyF6JVmar, Ze49bGd4ON

## Historical Sentinel IDs
- X41c4uB4k0, hj323oR3rw
