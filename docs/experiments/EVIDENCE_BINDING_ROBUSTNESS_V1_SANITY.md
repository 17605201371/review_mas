# Evidence Binding Robustness v1 Sanity

## Run

- Model: Qwen3.5-4B from `/reviewF/datasets/Qwen3___5-4B`
- Mode: S4
- Dataset: `outputs/subsets/state_hygiene_mixed_v2.parquet`
- Rows: 16 / 16 completed
- Output: `outputs/results_main/review_infer/evidence_binding_v1_mixed16.jsonl`
- Log: `evidence_binding_v1_mixed16.log`

## Code Sanity

- `py_compile` passed for modified runtime files before the run.
- Static merge test confirmed `claim-fallback-*` strong support is downgraded to `medium` while real claim strong support remains `strong`.
- Evidence context fields continued to appear in turn logs.

## Runtime Sanity

- No parse crash or stuck loop observed.
- `evidence_parse_error_count = 0`.
- `evidence_valid_payload_rate = 0.8980`.
- `binding_status_counts = {"bound_real_claim": 13}` for final strong support items.

## Caveat

The result jsonl does not carry gold labels in `ground_truth_decision`, so `accept_samples_with_2plus_real_strong_support` remains unavailable from this analyzer. The label-independent metric `rows_with_2plus_real_strong_support` is used instead.
