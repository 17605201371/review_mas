# Evidence JSON Robustness v1 Protocol

## Goal

This patch keeps the current `p25.1 + explicit recovery phase + Evidence Binding/Context` line and fixes one narrow failure mode: malformed Evidence Agent JSON should not immediately collapse into broad fallback evidence when recoverable structured evidence is already present.

## Scope

In scope:

- Evidence Agent parsing robustness.
- Partial recovery of complete `evidence_map` objects from malformed Evidence Agent JSON.
- Preventing normal Evidence fallback from running inside `recovery_patch` turns.
- Trace flags for `partial_json_recovery`.

Out of scope:

- No final decision changes.
- No recovery/sticky/throttle/gate changes.
- No validator/lifecycle changes.
- No prompt rework beyond the existing short-think Evidence prompt.
- No 9B runs.

## Implementation

1. `extract_tagged_json()` now strips nested markdown code fences inside `<json>...</json>` before parsing.
2. Evidence Agent parse failures try `extract_evidence_partial_payload()` before fallback, but only outside `recovery_patch` turns.
3. Partial recovery extracts complete JSON objects from `evidence_map` and `conflict_notes` arrays if the overall JSON is truncated.
4. `recovery_patch` turns no longer run normal Evidence fallback after parse failure; they go directly to patch-mode failure handling.

## Runtime Config

Recommended debug config from this round:

```bash
--mode s4
--max-turns 8
--manager-batch-size 4
--gpu-memory-utilization 0.66
--max-model-len 3072
--max-num-seqs 128
--max-tokens 768
```

`max_model_len=4096` was tested and rejected as a default because it slowed runs without improving support formation.
