# Coupled State Hygiene Simulation v1

**Input**: `outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Summary

| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | baseline |
| `C1_system_unresolved_meta_candidate` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `C2_system_unresolved_ungrounded_candidate` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `C3_unowned_unresolved_ungrounded_candidate` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `C4_oracle_negative_plus_support_guard` | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |

## 2. Flips

### C1_system_unresolved_meta_candidate

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### C2_system_unresolved_ungrounded_candidate

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### C3_unowned_unresolved_ungrounded_candidate

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### C4_oracle_negative_plus_support_guard

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`


## 3. Decision

No coupled non-oracle rule safely recovered accept.
Runtime state hygiene should still be deferred.
