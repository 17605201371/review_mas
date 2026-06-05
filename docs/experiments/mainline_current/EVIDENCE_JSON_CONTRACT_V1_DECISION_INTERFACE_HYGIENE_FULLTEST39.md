# Decision Interface Hygiene Simulation v1

**Input**: `outputs/results_main/review_infer/evidence_json_contract_v1_fulltest39_4b_merged.jsonl`
**Samples**: 39
**Runtime behavior changed**: no

## 1. Summary

| variant | acc | macro-F1 | accept R | reject R | pred A | pred R | flips | recovered A | false A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0 | 0 | 0 |
| `DI1_grounded_flaw_only` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0 | 0 | 0 |
| `DI2_grounded_flaw_stale_cleanup` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0 | 0 | 0 |
| `DI3_balanced_hygiene` | 0.7436 | 0.4265 | 0.0000 | 0.9667 | 1 | 38 | 1 | 0 | 1 |
| `DI4_confirmed_only_flaw` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0 | 0 | 0 |
| `DI5_lifecycle_cleanup` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0 | 0 | 0 |
| `DI_ORACLE_no_candidates_no_unresolved` | 0.7436 | 0.4265 | 0.0000 | 0.9667 | 1 | 38 | 1 | 0 | 1 |

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

- recovered_accept_ids: `[]`
- false_accept_ids: `['cklg91aPGk']`
- all_flips: `['cklg91aPGk']`

### DI4_confirmed_only_flaw

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### DI5_lifecycle_cleanup

- recovered_accept_ids: `[]`
- false_accept_ids: `[]`
- all_flips: `[]`

### DI_ORACLE_no_candidates_no_unresolved

- recovered_accept_ids: `[]`
- false_accept_ids: `['cklg91aPGk']`
- all_flips: `['cklg91aPGk']`


## 3. Blocker Distribution

### baseline

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `unresolved>=6` | 21 |
| `critical>=1` | 8 |
| `major>=2` | 3 |
| `major>0_blocks_accept` | 1 |
| `unresolved>3_blocks_accept` | 1 |

### DI1_grounded_flaw_only

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `unresolved>=6` | 21 |
| `major>0_blocks_accept` | 1 |
| `unresolved>3_blocks_accept` | 1 |

### DI2_grounded_flaw_stale_cleanup

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `unresolved>=6` | 16 |
| `major>0_blocks_accept` | 1 |

### DI3_balanced_hygiene

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `unresolved>=6` | 16 |
| `major>0_blocks_accept` | 1 |

### DI4_confirmed_only_flaw

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `unresolved>=6` | 21 |
| `unresolved>3_blocks_accept` | 1 |

### DI5_lifecycle_cleanup

| blocker | samples |
|---|---:|
| `strong<2` | 38 |
| `major>0_blocks_accept` | 1 |

### DI_ORACLE_no_candidates_no_unresolved

| blocker | samples |
|---|---:|
| `strong<2` | 38 |

## 4. Decision

- If all non-oracle variants still predict zero accepts, the immediate blocker is not a missing runtime controller. It is that final-decision inputs remain dominated by unresolved/strong-support/flaw blockers.
- If a non-oracle variant restores accept recall without false accepts on stable reject controls, that variant becomes the candidate for a minimal runtime state-hygiene fix.
- Oracle results are upper-bound diagnostics only and must not be treated as deployable policy.
