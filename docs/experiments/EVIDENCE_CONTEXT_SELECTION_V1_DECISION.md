# Evidence Context Selection v1 Decision

## Decision

**Do not keep Evidence Context Selection v1 as-is as the final mainline behavior.** Keep the diagnostics and helper direction, but v1 needs a follow-up before it can be considered retained.

## Why

v1 succeeds on the intended input-layer visibility check: Evidence Agent now receives section-aware contexts around method/results/table/conclusion regions instead of only the leading excerpt. However, the output-layer behavior is not yet safe enough.

Key results on the 16-row mixed subset:

- `visible_results_rate`: 0 -> 0.6186
- `visible_table_or_figure_rate`: 0 -> 0.7320
- `avg_evidence_context_chars`: 0 -> 2174.37 recorded chars
- `final_strong_support_total`: 4 -> 15
- `strong_support_on_real_claim`: 1 -> 4
- `strong_support_on_fallback_claim`: 3 -> 11
- `Evidence fallback_payload_count`: 15 -> 36
- `Evidence valid_json_rate`: 1.0 -> 0.8557
- `accept_samples_with_2plus_real_strong_support`: 0 -> 0

## Root Interpretation

The earliest input bottleneck is real: the old Evidence Agent context was too shallow. But simply expanding context makes the model produce more evidence attempts without reliably binding them to stable real claims. The next failure point is now evidence payload robustness and claim binding.

## Retain / Roll Back

- Retain: static context cleaner, preview tooling, and evidence context instrumentation.
- Do not yet retain: section-aware 2400-char Evidence context as the final runtime default without a follow-up robustness fix.
- Do not change: final decision, recovery controller, sticky/throttle/gate, or state hygiene runtime based on this result alone.

## Next Cut

Recommended next cut: **Evidence JSON Robustness + Real Claim Binding v1**. Keep the improved context idea, but constrain the Evidence Agent output to bind support only to existing real claim IDs when possible and reduce fallback payload creation.

Alternative if speed becomes the immediate blocker: run a smaller `max_length=1800` section-aware variant before robustness work, but only as a speed/quality ablation.
