# Evidence JSON Robustness v1 Decision

## Decision

Keep Evidence JSON Robustness v1.1.

## Reason

The patch reduces harmful fallback behavior without reducing the main positive-support metrics on mixed16:

- `evidence_fallback_payloads: 18 -> 8`
- `partial_json_recovery: 0 -> 3`
- `real_strong: 5 -> 5`
- `nonabs_strong: 5 -> 5`
- `fallback_strong: 0 -> 0`

This is exactly the desired behavior for a robustness patch: fewer malformed-output fallbacks, no new fallback strong support, and no regression in real-claim support.

## Not Solved

This does not solve accept collapse or produce more real strong support than the earlier v2 run. The remaining failure mode is evidence formation quality, not just parser robustness:

- Several Evidence Agent failures are role confusion under recovery patch mode.
- Some parse errors have no complete recoverable evidence object.
- Claim fallback still creates fallback claims in a few rows, which limits later evidence binding.

## Next Cut

Do not tune final decision and do not add controller constraints.

The next useful cut should be Claim/Evidence formation quality:

1. Reduce claim fallback rows by improving malformed claim salvage or claim prompt brevity.
2. Keep Evidence Agent on `3072/768` and the current partial recovery parser.
3. Evaluate whether claim fallback rows are the main reason real strong support stalls at `5`.

If the next step is runtime, prefer a small Claim JSON Robustness / Claim Fallback Restraint patch over more Evidence prompt tuning.
