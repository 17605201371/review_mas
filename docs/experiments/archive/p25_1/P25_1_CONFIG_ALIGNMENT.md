# P25.1 Config Alignment

## Result

Status: PASS for the critical runtime envelope used by the target observability Layer 2 run.

## Critical Fields

| key | baseline | candidate | status |
| --- | --- | --- | --- |
| mode | s4 | s4 | OK |
| model_path | /reviewF/datasets/Qwen3___5-9B | /reviewF/datasets/Qwen3___5-9B | OK |
| max_turns | 8 | 8 | OK |
| max_workers_per_turn | 2 | 2 | OK |
| manager_batch_size | 1 | 1 | OK |
| max_model_len | 3072 | 3072 | OK |
| max_tokens | 640 | 640 | OK |
| temperature | 0.2 | 0.2 | OK |
| top_p | 0.95 | 0.95 | OK |
| max_num_seqs | 128 | 128 | OK |
| gpu_memory_utilization | 0.94 | 0.94 | OK |
| seed | 20260423 | 20260423 | OK |

## Scope Difference

The candidate is a Layer 2 five-sample observability run, not a full 10-row benchmark. The subset difference is intentional for fast debugging. The purpose is field validation and target evolution diagnosis, not final performance comparison.
