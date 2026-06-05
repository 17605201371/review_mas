# State Hygiene Mixed v2 Protocol

**Purpose**: validate coupled state hygiene on a fresh accept/reject subset, not on the original 16-row focus set.

## 1. Dataset Source

- Source: `/reviewF/datasets/drmas_review_eval100/test.parquet`
- Source size: 100 samples
- Source label distribution: 39 Accept / 61 Reject
- Exclusion: all ids from `outputs/subsets/state_hygiene_4b_focus_meta.json`

## 2. Selected Subset

- Output parquet: `outputs/subsets/state_hygiene_mixed_v2.parquet`
- Output meta: `outputs/subsets/state_hygiene_mixed_v2_meta.json`
- Size: 16 samples
- Composition: 8 fresh Accept + 8 fresh Reject

## 3. Selected IDs

### fresh_accept

- `cWEfRkYj46`
- `nrvoWOWcyg`
- `VEJzjAvaIy`
- `nrRkAAAufl`
- `IdAyXxBud7`
- `pOq9vDIYev`
- `giU9fYGTND`
- `cpGPPLLYYx`

### fresh_reject

- `xYzOkOGD96`
- `bcHty5VvkQ`
- `k243qi7S50`
- `GSckuQMzBG`
- `JdWpIe70FL`
- `YvWuac63bg`
- `qgyF6JVmar`
- `77plFC53J5`

## 4. Recommended 4B Run

```bash
conda run -n DrMAS-qwen35 python -u -m agent_system.inference.review_runner   --dataset-path outputs/subsets/state_hygiene_mixed_v2.parquet   --model-path /reviewF/datasets/Qwen3___5-4B   --temperature 0.2   --top-p 0.95   --mode s4   --max-turns 8   --max-workers-per-turn 2   --manager-batch-size 4   --gpu-memory-utilization 0.60   --max-num-seqs 128   --max-model-len 3072   --max-tokens 640   --output-path outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl   2>&1 | tee p25_1_state_hygiene_mixed_v2.log
```

## 5. Validation Goal

After running, re-run the existing offline audit/simulation scripts with:

- `--results-path outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl`
- `--meta-path outputs/subsets/state_hygiene_mixed_v2_meta.json`
- `--selected-only`

The key question is whether `C3_unowned_unresolved_ungrounded_candidate` remains safe on a fresh mixed subset.
