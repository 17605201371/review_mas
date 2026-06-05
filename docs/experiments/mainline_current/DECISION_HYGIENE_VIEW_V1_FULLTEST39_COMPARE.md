# Decision Hygiene View v1 Fulltest39 4B Analysis

Input: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl`

## Summary

| metric | value |
|---|---:|
| `rows` | 39 |
| `evidence_calls` | 233 |
| `rows_with_context` | 39 |
| `visible_method_rate` | 0.1845 |
| `visible_results_rate` | 0.7768 |
| `visible_conclusion_rate` | 0.4850 |
| `visible_table_or_figure_rate` | 0.8627 |
| `avg_evidence_context_chars` | 2241.5966 |
| `evidence_valid_payload_rate` | 0.8670 |
| `evidence_fallback_payload_count` | 47 |
| `evidence_parse_error_count` | 0 |
| `raw_positive_evidence_mentions` | 96 |
| `raw_insufficient_excerpt_mentions` | 2 |
| `final_strong_support_total` | 20 |
| `strong_support_on_real_claim` | 20 |
| `strong_support_on_fallback_claim` | 0 |
| `unbound_strong_support` | 0 |
| `fallback_extraction_strong_support` | 0 |
| `evidence_binding_error_count` | 0 |
| `strong_support_binding_precision` | 1.0000 |
| `binding_status_counts` | {'bound_real_claim': 20} |
| `rows_with_2plus_real_strong_support` | 7 |
| `accept_samples_with_2plus_real_strong_support` | 0 |

## Per Row

| paper_id | gold | final | evidence calls | strong real | strong total |
|---|---|---|---:|---:|---:|
| ye3NrNrYOY | None | reject | 4 | 2 | 2 |
| WNxlJJIEVj | None | reject | 6 | 0 | 0 |
| uOrfve3prk | None | reject | 6 | 0 | 0 |
| hj323oR3rw | None | reject | 3 | 0 | 0 |
| 7Dub7UXTXN | None | reject | 4 | 0 | 0 |
| 9zEBK3E9bX | None | reject | 7 | 0 | 0 |
| XyB4VvF01X | None | accept | 7 | 3 | 3 |
| GE6iywJtsV | None | reject | 7 | 0 | 0 |
| QAAsnSRwgu | None | reject | 7 | 0 | 0 |
| WpXq5n8yLb | None | reject | 6 | 0 | 0 |
| X41c4uB4k0 | None | reject | 4 | 0 | 0 |
| NnExMNiTHw | None | reject | 7 | 1 | 1 |
| gzqrANCF4g | None | accept | 7 | 3 | 3 |
| a6SntIisgg | None | reject | 7 | 0 | 0 |
| cklg91aPGk | None | reject | 5 | 0 | 0 |
| HPuLU6q7xq | None | reject | 4 | 0 | 0 |
| fGXyvmWpw6 | None | reject | 3 | 0 | 0 |
| QAgwFiIY4p | None | accept | 7 | 3 | 3 |
| KI9NqjLVDT | None | reject | 7 | 0 | 0 |
| 1HCN4pjTb4 | None | reject | 7 | 0 | 0 |
| LebzzClHYw | None | reject | 4 | 0 | 0 |
| BXY6fe7q31 | None | reject | 4 | 0 | 0 |
| TPAj63ax4Y | None | accept | 7 | 2 | 2 |
| mHv6wcBb0z | None | reject | 7 | 0 | 0 |
| xUe1YqEgd6 | None | reject | 7 | 2 | 2 |
| jVEoydFOl9 | None | reject | 7 | 0 | 0 |
| YXn76HMetm | None | reject | 7 | 0 | 0 |
| KOUAayk5Kx | None | reject | 7 | 0 | 0 |
| XH3OiIhtvf | None | reject | 3 | 0 | 0 |
| ZHr0JajZfH | None | reject | 7 | 1 | 1 |
| WLgbjzKJkk | None | reject | 5 | 0 | 0 |
| 9JRsAj3ymy | None | reject | 7 | 0 | 0 |
| rEqETC88RY | None | reject | 4 | 0 | 0 |
| aTBE70xiFw | None | reject | 7 | 0 | 0 |
| LieTse3fQB | None | reject | 7 | 0 | 0 |
| kam84eEmub | None | accept | 7 | 2 | 2 |
| N0isTh3rml | None | reject | 7 | 1 | 1 |
| 2L7KQ4qbHi | None | reject | 7 | 0 | 0 |
| aRxLDcxFcL | None | reject | 7 | 0 | 0 |


## Decision Health Addendum

The context/binding metrics are positive, but fulltest39 shows the original hygiene accept rule was too permissive.

| Rule | Accuracy | Macro-F1 | Pred Accept | True Accept | False Accept | False Reject | Reject Recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| Always reject | 0.7692 | 0.4348 | 0 | 0 | 0 | 9 | 1.0000 |
| Original hygiene rule (`support >= 2`) | 0.6923 | 0.4777 | 5 | 1 | 4 | 8 | 0.8667 |
| Patched hygiene rule (`support >= 3`) | 0.7436 | 0.5076 | 3 | 1 | 2 | 8 | 0.9333 |

Decision: keep Evidence Binding Robustness v1 and final-view hygiene, but tighten accept to require at least 3 real strong support items. This does not solve accept recovery completely; it is a safety patch that prevents two shallow support signals from flipping reject papers.
