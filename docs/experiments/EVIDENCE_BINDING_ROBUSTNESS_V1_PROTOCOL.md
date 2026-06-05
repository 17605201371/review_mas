# Evidence Binding Robustness v1 Protocol

## Goal

Evidence Context Selection v1 proved that shallow evidence context was a real input bottleneck, but it also amplified structured binding failures: strong support increased mostly on fallback claims. Evidence Binding Robustness v1 fixes that narrow failure mode without changing final decision, recovery, sticky/throttle/gate, reward, or state hygiene.

## Changes

- Evidence prompt now exposes `allowed_claim_ids` through the Evidence State Slice and instructs the model to bind evidence only to existing real claim ids.
- Evidence items may include `binding_confidence` and `binding_rationale` for analysis.
- Evidence merge validates claim bindings before writing into ReviewState.
- Evidence bound to missing, invalid, or `claim-fallback-*` ids is marked as `unbound`, `invalid_claim_id`, or `fallback_bound` and cannot remain `strength=strong`.
- `source=fallback-extraction` evidence is marked `binding_status=fallback_unverified` and cannot remain `strength=strong`.
- Fallback Evidence Agent output now prefers existing real claims and emits unresolved questions instead of creating fallback strong support when no real claim exists.

## Non-Changes

- No final decision threshold changes.
- No recovery controller changes.
- No sticky/throttle/gate changes.
- No fallback suppression beyond evidence fallback down-weighting.
- No candidate flaw or unresolved lifecycle runtime changes.

## Evaluation

The evaluation uses the fixed 16-row mixed subset and compares three conditions:

1. Old p25.1 mixed baseline.
2. Evidence Context Selection v1.
3. Evidence Binding Robustness v1.

Primary metrics are real-claim support, fallback-claim support, binding precision, and fallback payload count. Final accept/reject is reported only as a health check.
