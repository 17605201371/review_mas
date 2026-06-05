# Evidence Binding Robustness v1 Decision

## Decision

**Keep Evidence Binding Robustness v1.**

This is a successful repair of the failure mode exposed by Evidence Context Selection v1. It does not solve final decision collapse, but it makes the evidence state materially cleaner and prevents fallback strong support from being treated as real positive evidence.

## Evidence

On the fixed 16-row mixed subset:

- `strong_support_on_fallback_claim`: 11 -> 0 versus Context v1.
- `strong_support_on_real_claim`: 4 -> 13 versus Context v1.
- `strong_support_binding_precision`: 0.2667 -> 1.0.
- `rows_with_2plus_real_strong_support`: 2 -> 4.
- `evidence_fallback_payload_count`: 36 -> 16.
- `fallback_extraction_strong_support`: 0.
- `evidence_binding_error_count`: 0.

## What It Does Not Solve

All 16 rows still end with `reject`. That is not a reason to reject this patch, because this patch intentionally does not modify final decision. The remaining bottleneck has shifted downstream: final decision and/or flaw/unresolved lifecycle still over-weights negative state even when real positive evidence is now present.

## Next Cut

Recommended next step: **State Hygiene / Flaw-Unresolved Lifecycle v1 on top of clean real-claim support**.

Do not tune final decision threshold yet. First audit the rows that now have 2+ real strong supports but still reject, and identify which active flaw, unresolved question, evidence gap, or conflict keeps them rejected.

## Keep / Rollback

- Keep: allowed claim id prompt constraint, evidence binding validation, fallback evidence down-weighting, binding metrics.
- Do not roll back unless a later larger subset shows real-claim support collapses or fallback payloads rise again.
