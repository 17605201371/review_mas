# Recovery Push Source Audit

## Layer 2 Summary

| metric | value |
| --- | ---: |
| rows | 5 |
| turns | 36 |
| recovery_push_triggered_turns | 4 |
| patch_emitted_count | 3 |
| patch_committed_count | 2 |

## Recovery Push Source Distribution

| source | count | target quality |
| --- | ---: | --- |
| sticky_recovery_bias | 4 | 3 narrow_real_target, 1 empty_target |

## Interpretation

The observed recovery pushes in this Layer 2 run were not driven by sanitize bloat or fallback targets. The only recorded push source was `sticky_recovery_bias`, and most of those pushes were on `narrow_real_target`. This is a warning against immediately adding a broad global progression gate: in this subset, the recovery pushes that actually occurred were not broad/fallback recovery pushes.
