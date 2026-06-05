# State Hygiene Mixed v2 Decision

## Run

- Dataset: `outputs/subsets/state_hygiene_mixed_v2.parquet`
- Source pool: `/reviewF/datasets/drmas_review_eval100/test.parquet`
- Composition: 16 samples, 8 fresh Accept + 8 fresh Reject, excluding the previous 16-sample focus set.
- Model: Qwen3.5-4B
- Runtime: S4, `max_turns=8`, `max_workers_per_turn=2`, `manager_batch_size=4`, `max_num_seqs=128`.
- Result: `outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl`
- Log: `p25_1_state_hygiene_mixed_v2.log`

## Result Summary

The mixed v2 run reproduced the always-reject symptom on a fresh balanced subset.

| metric | value |
|---|---:|
| samples | 16 |
| gold accept | 8 |
| gold reject | 8 |
| predicted accept | 0 |
| predicted reject | 16 |
| accuracy | 0.5000 |
| macro-F1 | 0.3333 |
| accept recall | 0.0000 |
| reject recall | 1.0000 |

The coupled state hygiene simulation did not recover any accept sample on this subset.

| rule | recovered accept | false accept | decision |
|---|---:|---:|---|
| C1 system unresolved + meta candidate | 0 | 0 | no gain |
| C2 system unresolved + ungrounded candidate | 0 | 0 | no gain |
| C3 unowned unresolved + ungrounded candidate | 0 | 0 | no gain |
| C4 oracle negative + support guard | 0 | 0 | no gain |

## Main Finding

The previous C3 result does not generalize to the fresh mixed v2 subset. The new subset shows a stronger upstream bottleneck: the system often fails to form usable positive support at all.

Key evidence:

- `strong<2` appears in 15/16 samples.
- `unresolved>=6` appears in 15/16 samples.
- `unsupported_with_strong_support` is only 2 total.
- `unsupported_with_2plus_strong` is only 1 total.
- In the C3 casebook, `support_count_after_C3` is 0 for all 8 fresh Accept samples.

This means negative cleanup alone cannot recover accept decisions when the ReviewState never records enough non-fallback, grounded positive support.

## Interpretation

The current always-reject failure has at least two layers:

1. Negative lifecycle burden: unresolved items and ungrounded candidate flaws can suppress accept when positive support exists.
2. Positive support formation failure: for many fresh accept samples, grounded strong support is not extracted or retained in the first place.

The mixed v2 subset is dominated by the second layer. Therefore, immediately implementing `Coupled State Hygiene v1` would be premature. It may help the earlier focus set, but it will not solve this broader failure mode.

## Next Direction

Pause runtime state hygiene fixes until the positive support path is audited.

Recommended next single step:

**Positive Support Formation Audit**

It should answer:

- Are accept papers missing claims, missing evidence, or losing evidence during state merge?
- Are strong supports being emitted by workers but not committed into `evidence_map`?
- Are supports attached to fallback claims and then discarded by the non-fallback support guard?
- Are positive supports present in final reports but absent from `ReviewState`?
- Which stage first loses the positive evidence: claim extraction, evidence extraction, parser, merge, or final decision?

Do not tune final decision thresholds yet. The core problem on this fresh subset is not only a reject threshold; it is insufficient grounded positive evidence in ReviewState.
