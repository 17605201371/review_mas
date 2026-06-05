# Decision Hygiene View v1 Fulltest39 Decision Review

## Scope

This review uses the 4B fulltest39 run from the current `p25.1 + explicit recovery phase + Evidence Binding Robustness v1 + Decision Hygiene View v1` code path.

- Result JSONL: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl`
- Binding/context analysis: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b_analysis.json`
- Decision-health simulation: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_patched_rule_sim.json`

## Main Finding

Evidence Binding Robustness v1 remains positive on fulltest39, but the original Decision Hygiene accept rule was too permissive.

Binding health is strong:

| Metric | Value |
|---|---:|
| `final_strong_support_total` | 20 |
| `strong_support_on_real_claim` | 20 |
| `strong_support_on_fallback_claim` | 0 |
| `unbound_strong_support` | 0 |
| `fallback_extraction_strong_support` | 0 |
| `strong_support_binding_precision` | 1.0 |
| `rows_with_2plus_real_strong_support` | 7 |

The failure is not fallback binding anymore. The failure is that final-view hygiene can over-accept reject papers when the accept rule only requires two real strong support items.

## Decision Health

| Rule | Accuracy | Macro-F1 | Pred Accept | True Accept | False Accept | False Reject | Reject Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Always reject | 0.7692 | 0.4348 | 0 | 0 | 0 | 9 | 1.0000 |
| Original hygiene rule (`support >= 2`) | 0.6923 | 0.4777 | 5 | 1 | 4 | 8 | 0.8667 |
| Patched hygiene rule (`support >= 3`) | 0.7436 | 0.5076 | 3 | 1 | 2 | 8 | 0.9333 |

The patched rule is not a complete solution, but it removes the two weakest false accepts while preserving the only recovered accept in this fulltest run.

## Affected Accept Rows

Original hygiene rule accepted:

- True accept: `gzqrANCF4g`
- False accepts: `XyB4VvF01X`, `QAgwFiIY4p`, `TPAj63ax4Y`, `kam84eEmub`

After requiring at least 3 real strong supports, accepted rows become:

- True accept: `gzqrANCF4g`
- False accepts: `XyB4VvF01X`, `QAgwFiIY4p`

Rows `TPAj63ax4Y` and `kam84eEmub` return to reject because they only had two real strong support items.

## Interpretation

This confirms three points:

1. Evidence Binding Robustness v1 should be kept. Strong support no longer leaks into fallback claims.
2. Decision Hygiene View should remain a final-view mechanism, not live-state mutation.
3. The accept rule must require stronger positive evidence than two shallow support items.

This also shows the remaining bottleneck: support quantity alone is insufficient. The false accepts that remain have 3 real strong support items, so the next diagnostic should inspect support quality and claim-level evidence depth, not controller routing.

## Code Decision

A minimal safety patch was applied:

```python
if strong_support >= 3 and major_flaws == 0 and unresolved <= 3:
    return "accept"
```

This keeps hygiene-derived accept possible but makes it harder to flip reject papers on weak positive evidence.

## Next Step

Do not return to sticky/throttle/progression gate. The next useful step is an offline analysis of accepted/false-accepted rows:

- whether strong supports are independent or duplicate evidence;
- whether support is distributed thinly across claims or concentrated on a real central claim;
- whether a paper still has grounded unresolved concerns that hygiene is over-deferring;
- whether support evidence is method/result-level or generic abstract-level.

Only after that should we consider a `Support Quality View v1` or `Evidence Independence v1` check.
