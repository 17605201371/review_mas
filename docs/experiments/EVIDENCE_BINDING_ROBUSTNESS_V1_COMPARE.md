# Evidence Binding Robustness v1 Compare

## Metric Table

| Metric | Old baseline | Context v1 | Binding v1 | Context->Binding delta |
|---|---:|---:|---:|---:|
| Evidence fallback payloads | 15 | 36 | 16 | -20 |
| Evidence valid payload rate | 1.0000 | 0.8557 | 0.8980 | 0.0423 |
| Raw positive evidence mentions | 23 | 20 | 31 | 11 |
| Final strong support total | 4 | 15 | 13 | -2 |
| Real-claim strong support | 1 | 4 | 13 | 9 |
| Fallback-claim strong support | 3 | 11 | 0 | -11 |
| Rows with 2+ real strong support | 0 | 2 | 4 | 2 |
| Strong support binding precision | 0.2500 | 0.2667 | 1.0000 | 0.7333 |
| Fallback-extraction strong support | 0 | 0 | 0 | 0 |
| Evidence binding error count | 0 | 0 | 0 | 0 |
| Visible results rate | 0.0000 | 0.6186 | 0.6020 | -0.0165 |
| Visible table/figure rate | 0.0000 | 0.7320 | 0.7143 | -0.0177 |

## Interpretation

Evidence Binding Robustness v1 fixes the main failure introduced by Evidence Context v1: strong support no longer accumulates on fallback claims. Compared with Context v1, fallback-claim strong support drops from 11 to 0, real-claim strong support rises from 4 to 13, and binding precision rises from 0.2667 to 1.0.

The change also reduces Evidence fallback payload count from 36 to 16, nearly back to old baseline 15, while keeping section-aware context visibility. Rows with at least two real strong support items increase from 2 to 4.

Final decisions still all resolve to reject, so this does not solve decision collapse by itself. It does, however, make the positive evidence state substantially cleaner and safer for the next state hygiene / flaw-unresolved lifecycle step.
