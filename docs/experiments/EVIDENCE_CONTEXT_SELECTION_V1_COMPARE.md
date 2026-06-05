# Evidence Context Selection v1 Compare

## Summary

Evidence Context Selection v1 improves visibility into evidence-rich sections, but it does not yet solve positive support formation. It increases total strong support and real-claim strong support, while also increasing fallback-bound support and Evidence fallback payloads.

## Metric Table

| Metric | Old baseline | v1 | Delta |
|---|---:|---:|---:|
| visible_results_rate | 0 | 0 | 0 |
| visible_method_rate | 0 | 0 | 0 |
| visible_conclusion_rate | 0 | 0 | 0 |
| visible_table_or_figure_rate | 0 | 0 | 0 |
| avg_evidence_context_chars | 0 | 0 | 0 |
| Evidence valid_json_rate | 0 | 0 | 0 |
| Evidence fallback_payload_count | 0 | 0 | 0 |
| raw_positive_evidence_mentions | 0 | 0 | 0 |
| final_strong_support_total | 0 | 0 | 0 |
| strong_support_on_real_claim | 0 | 0 | 0 |
| strong_support_on_fallback_claim | 0 | 0 | 0 |
| accept_samples_with_2plus_real_strong_support | 0 | 0 | 0 |
| raw_insufficient_excerpt_mentions | 0 | 0 | 0 |

## Interpretation

- Context visibility works: v1 records non-zero method/results/conclusion/table visibility, while old logs had no visibility instrumentation and old Evidence Agent used the short leading excerpt path.
- Positive support partially improves: `final_strong_support_total` increases from 4 to 15 and `strong_support_on_real_claim` from 1 to 4.
- The improvement is not clean enough: `strong_support_on_fallback_claim` also increases from 3 to 11, so most new support is still attached to fallback claims rather than stable real claims.
- Evidence robustness regresses: valid payload rate drops from 1.0 to 0.8557 and fallback payload count rises from 15 to 36.
- Accept recovery is still absent: `accept_samples_with_2plus_real_strong_support` remains 0 and all 16 rows still end with reject.

## Decision Signal

Do not treat v1 as a complete fix. It validates that evidence context visibility was a real bottleneck, but the next cut should focus on Evidence JSON/grounding robustness or target binding, not final decision thresholds.
