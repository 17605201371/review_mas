# Support Quality View v1 Audit

## Scope

This audit uses the fulltest39 4B JSONL produced by the current mainline. It does not rerun the model and does not change live ReviewState behavior.

## Main Conclusion

Evidence Binding is now clean, but the remaining false accepts show that `real_strong_support_total` is not enough as an accept signal. The accepted rows are driven by abstract-level support, often one support per claim, with no method/result-level corroboration. Therefore the next research/code direction should be support quality and evidence independence, not sticky/throttle/controller logic.

## Patched Accept Rows

| paper_id | gold | pred | support_total | max_per_claim | claims_supported | claims_2plus | abstract | non_abstract | open_unresolved | conflicts | support_by_claim |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `XyB4VvF01X` | reject | accept | 3 | 1 | 3 | 0 | 3 | 0 | 2 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |
| `gzqrANCF4g` | accept | accept | 3 | 1 | 3 | 0 | 3 | 0 | 3 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |
| `QAgwFiIY4p` | reject | accept | 3 | 1 | 3 | 0 | 3 | 0 | 3 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |

## Rows With At Least Two Real Strong Supports

| paper_id | gold | pred | support_total | max_per_claim | claims_supported | claims_2plus | abstract | non_abstract | open_unresolved | conflicts | support_by_claim |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `ye3NrNrYOY` | reject | reject | 2 | 1 | 2 | 0 | 1 | 1 | 6 | 2 | `{'claim-1': 1, 'claim-2': 1}` |
| `XyB4VvF01X` | reject | accept | 3 | 1 | 3 | 0 | 3 | 0 | 2 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |
| `gzqrANCF4g` | accept | accept | 3 | 1 | 3 | 0 | 3 | 0 | 3 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |
| `QAgwFiIY4p` | reject | accept | 3 | 1 | 3 | 0 | 3 | 0 | 3 | 0 | `{'claim-1': 1, 'claim-2': 1, 'claim-3': 1}` |
| `TPAj63ax4Y` | reject | reject | 2 | 2 | 1 | 1 | 1 | 1 | 2 | 0 | `{'claim-2': 2}` |
| `xUe1YqEgd6` | reject | reject | 2 | 1 | 2 | 0 | 2 | 0 | 5 | 4 | `{'claim-1': 1, 'claim-2': 1}` |
| `kam84eEmub` | reject | reject | 2 | 1 | 2 | 0 | 1 | 1 | 2 | 0 | `{'claim-2': 1, 'claim-3': 1}` |

## Interpretation

- `strong_support_on_fallback_claim = 0`, so the old fallback-binding pollution is not the current failure.
- The false accepts that remain are not caused by unbound support; they are caused by positive evidence that is too shallow for final recommendation.
- A pure threshold rule cannot safely recover more accept rows from current state features. Offline search found that zero-false-accept rules collapse back to always-reject on this 39-row set.
- The useful next step is to score support quality: source section, independence, duplicate evidence, and whether support backs a central claim rather than peripheral abstract claims.

## Next Cut

Implement only diagnostic support-quality fields first. A future `Support Quality View v1` should not accept based on total support count alone; it should require stronger evidence quality such as non-abstract/result-level support or independent corroboration. If current 4B outputs cannot produce such evidence, the bottleneck goes back to Evidence Agent evidence formation rather than final decision.
