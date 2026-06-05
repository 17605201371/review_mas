# Lifecycle Provenance Rule Simulation v1

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Rule Summary

| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | baseline |
| `decision_grounded_only` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `R1_close_system_unresolved` | 0.3750 | 0.2727 | 0.0000 | 0.8571 | 1 | 15 | 0 | 1 | reject |
| `R2_downgrade_meta_ungrounded_candidates` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `R3_close_system_and_meta_candidates` | 0.3750 | 0.2727 | 0.0000 | 0.8571 | 1 | 15 | 0 | 1 | reject |
| `R4_targeted_lifecycle` | 0.3750 | 0.2727 | 0.0000 | 0.8571 | 1 | 15 | 0 | 1 | reject |
| `R5_targeted_plus_reconcile` | 0.3750 | 0.2727 | 0.0000 | 0.8571 | 1 | 15 | 0 | 1 | reject |

## 2. Flips

### decision_grounded_only

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### R1_close_system_unresolved

- recovered_accept_ids: `[]`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['aTBE70xiFw']`

### R2_downgrade_meta_ungrounded_candidates

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### R3_close_system_and_meta_candidates

- recovered_accept_ids: `[]`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['aTBE70xiFw']`

### R4_targeted_lifecycle

- recovered_accept_ids: `[]`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['aTBE70xiFw']`

### R5_targeted_plus_reconcile

- recovered_accept_ids: `[]`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['aTBE70xiFw']`


## 3. Decision

No non-oracle provenance rule recovered accept without false accepts.

Do not implement runtime lifecycle cleanup yet. The current state lacks enough positive evidence/support separation; cleanup-only rules remain unsafe or ineffective.
