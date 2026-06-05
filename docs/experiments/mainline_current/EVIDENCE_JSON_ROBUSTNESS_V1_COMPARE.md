# Evidence JSON Robustness v1 Compare

## Runs

| run | rows | config | note |
|---|---:|---|---|
| `evidence_context_v2_mixed16` | 16 | `3072/640` | pre-robustness Evidence Context v2 |
| `evidence_context_v2_1_mixed16_3072_768` | 16 | `3072/768` | longer output budget |
| `evidence_json_robustness_v1_1_mixed16` | 16 | `3072/768` | partial JSON recovery + no evidence fallback in recovery patch mode |

## Aggregate Metrics

| metric | v2 `3072/640` | v2.1 `3072/768` | robustness v1.1 |
|---|---:|---:|---:|
| claim_parse_errors | 3 | 3 | 3 |
| claim_fallback_payloads | 3 | 3 | 3 |
| evidence_parse_errors | 25 | 18 | 16 |
| evidence_fallback_payloads | 25 | 18 | 8 |
| partial_json_recovery | 0 | 0 | 3 |
| fallback_claims | 9 | 9 | 9 |
| real_strong | 8 | 5 | 5 |
| nonabs_strong | 8 | 5 | 5 |
| empirical_strong | 5 | 5 | 4 |
| fallback_strong | 0 | 0 | 0 |

## Interpretation

Evidence JSON Robustness v1.1 is a precision/cleanup improvement rather than a support-formation breakthrough.

Positive signals:

- Evidence fallback payloads dropped from `18` to `8` relative to the same `3072/768` config.
- Partial JSON recovery fired `3` times.
- Real/non-abstract strong support stayed at `5`, so the cleanup did not damage positive evidence formation.
- Fallback strong support stayed at `0`, preserving the Evidence Binding Robustness invariant.

Limits:

- Real strong support did not recover to the earlier `v2 3072/640` level of `8`.
- Evidence parse errors remain non-trivial (`16`), because many failures are role/prompt confusion or no usable JSON, not just truncation.

## Config Finding

`max_model_len=4096` was slower and not better. The better tuning is `max_model_len=3072`, `max_tokens=768`.
