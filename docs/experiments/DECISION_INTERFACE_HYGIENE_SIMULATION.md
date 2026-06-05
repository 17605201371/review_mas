# Decision Interface Hygiene Simulation v1

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Summary

| variant | acc | macro-F1 | accept R | reject R | pred A | pred R | flips | recovered A | false A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | 0 |
| `DI1_grounded_flaw_only` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | 0 |
| `DI2_grounded_flaw_stale_cleanup` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | 0 |
| `DI3_balanced_hygiene` | 0.4375 | 0.3766 | 0.1111 | 0.8571 | 2 | 14 | 2 | 1 | 1 |
| `DI4_confirmed_only_flaw` | 0.4375 | 0.3043 | 0.0000 | 1.0000 | 0 | 16 | 0 | 0 | 0 |
| `DI5_lifecycle_cleanup` | 0.3750 | 0.2727 | 0.0000 | 0.8571 | 1 | 15 | 1 | 0 | 1 |
| `DI_ORACLE_no_candidates_no_unresolved` | 0.5625 | 0.5152 | 0.2222 | 1.0000 | 2 | 14 | 2 | 2 | 0 |

## 2. Key Flips

### DI1_grounded_flaw_only

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### DI2_grounded_flaw_stale_cleanup

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### DI3_balanced_hygiene

- recovered_accept_ids: `['QAAsnSRwgu']`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['QAAsnSRwgu', 'aTBE70xiFw']`

### DI4_confirmed_only_flaw

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### DI5_lifecycle_cleanup

- recovered_accept_ids: `[]`
- false_accept_ids: `['aTBE70xiFw']`
- all_flips: `['aTBE70xiFw']`

### DI_ORACLE_no_candidates_no_unresolved

- recovered_accept_ids: `['QAAsnSRwgu', 'KI9NqjLVDT']`
- false_accept_ids: `[]`
- all_flips: `['QAAsnSRwgu', 'KI9NqjLVDT']`


## 3. Blocker Distribution

### baseline

| blocker | samples |
|---|---:|
| `unresolved>=6` | 14 |
| `strong<2` | 12 |
| `critical>=1` | 8 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `major>=2` | 2 |

### DI1_grounded_flaw_only

| blocker | samples |
|---|---:|
| `unresolved>=6` | 14 |
| `strong<2` | 12 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `critical>=1` | 1 |

### DI2_grounded_flaw_stale_cleanup

| blocker | samples |
|---|---:|
| `strong<2` | 12 |
| `unresolved>=6` | 10 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `critical>=1` | 1 |

### DI3_balanced_hygiene

| blocker | samples |
|---|---:|
| `strong<2` | 12 |
| `unresolved>=6` | 10 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `critical>=1` | 1 |

### DI4_confirmed_only_flaw

| blocker | samples |
|---|---:|
| `unresolved>=6` | 14 |
| `strong<2` | 12 |
| `unresolved>3_blocks_accept` | 4 |
| `critical>=1` | 1 |

### DI5_lifecycle_cleanup

| blocker | samples |
|---|---:|
| `strong<2` | 12 |
| `major>0_blocks_accept` | 2 |
| `critical>=1` | 1 |

### DI_ORACLE_no_candidates_no_unresolved

| blocker | samples |
|---|---:|
| `strong<2` | 12 |
| `critical>=1` | 1 |

## 4. Decision

- If all non-oracle variants still predict zero accepts, the immediate blocker is not a missing runtime controller. It is that final-decision inputs remain dominated by unresolved/strong-support/flaw blockers.
- If a non-oracle variant restores accept recall without false accepts on stable reject controls, that variant becomes the candidate for a minimal runtime state-hygiene fix.
- Oracle results are upper-bound diagnostics only and must not be treated as deployable policy.

## 5. Lifecycle Cleanup Interpretation

`DI5_lifecycle_cleanup` is intentionally closer to the proposed unresolved/candidate lifecycle cleanup: it closes weak/system unresolved items and downgrades ungrounded candidate flaws before applying a grounded, candidate-weighted decision rule. It still fails: it flips only `aTBE70xiFw`, which is a gold reject, and recovers no accept.

This means the next runtime fix must not be a broad label-based cleanup. The lifecycle problem is real, but the cleanup conditions need to be more targeted:

- Closing weak/system unresolved removes a blocker, but many accept samples still fail `strong<2`.
- Downgrading all ungrounded candidates is unsafe because at least one reject control depends on an ungrounded-but-useful negative signal under the current state representation.
- The oracle result remains informative only as an upper bound: correct accept recovery requires resolving candidate/unresolved state together with support extraction, not just lowering decision thresholds.

