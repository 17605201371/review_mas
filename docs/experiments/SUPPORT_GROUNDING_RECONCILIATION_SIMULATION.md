# Support Grounding + Claim-Status Reconciliation Simulation v1

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Summary

| rule | acc | macro-F1 | accept R | reject R | pred A | pred R | recovered A | false A | decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | baseline |
| `SG1_nonfallback_support` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `SG2_reconcile_status` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `SG3_reconcile_plus_soft_unresolved` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | reject |
| `SG4_oracle_negatives_with_support_guard` | 0.5625 | 0.5152 | 0.2222 | 1.0000 | 2 | 14 | 2 | 0 | candidate |

## 2. Flips

### SG1_nonfallback_support

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### SG2_reconcile_status

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### SG3_reconcile_plus_soft_unresolved

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### SG4_oracle_negatives_with_support_guard

- recovered_accept_ids: `['QAAsnSRwgu', 'KI9NqjLVDT']`
- false_accept_ids: `[]`
- all_flips: `['QAAsnSRwgu', 'KI9NqjLVDT']`


## 3. Rule Decision

Safe offline candidates: `['SG4_oracle_negatives_with_support_guard']`.
Inspect case-level support before runtime implementation.

## 4. Interpretation

The support-side simulation does not justify a standalone runtime support fix:

- `SG1_nonfallback_support`, `SG2_reconcile_status`, and `SG3_reconcile_plus_soft_unresolved` recover no accept samples.
- `SG4_oracle_negatives_with_support_guard` recovers `QAAsnSRwgu` and `KI9NqjLVDT` without false accepts, but it depends on oracle removal of candidate flaws and unresolved questions.

This means positive support separation is necessary but not sufficient. The system needs a coupled fix: negative lifecycle objects must be validated/closed, while positive support must be counted only when attached to non-fallback real claims.

## 5. Decision

Do not implement support reconciliation alone. The next candidate is a combined offline protocol:

**Coupled State Hygiene Simulation v1**

Required ingredients:

1. Non-fallback support accounting.
2. Claim-status reconciliation for non-fallback strong support with no strong contradiction.
3. Conservative unresolved/candidate lifecycle cleanup.
4. Safety guard that rejects fallback-bound positive support, especially `aTBE70xiFw`.

Only if the coupled non-oracle rule recovers accept without false accepts should runtime state hygiene be implemented.

