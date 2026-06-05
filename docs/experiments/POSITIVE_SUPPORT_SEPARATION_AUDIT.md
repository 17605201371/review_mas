# Positive Evidence / Support Separation Audit v1

**Input**: `/root/zssmas_mainline/outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**Samples**: 16
**Runtime behavior changed**: no

## 1. Aggregate Support Counts

| metric | count |
|---|---:|
| `claim_count` | 32 |
| `evidence_count` | 51 |
| `fallback_strong_claim_count` | 4 |
| `strong_2plus_claim_count` | 2 |
| `strong_contradiction_claim_count` | 0 |
| `strong_lt_2_blocker_samples` | 12 |
| `strong_positive_fallback_claim` | 6 |
| `strong_positive_meta_or_generic` | 0 |
| `strong_positive_on_supported_claim` | 1 |
| `strong_positive_on_uncertain_claim` | 0 |
| `strong_positive_on_unsupported_claim` | 7 |
| `strong_positive_total` | 14 |
| `strong_support_claim_count` | 12 |
| `unsupported_strong_claim_count` | 11 |

## 2. Support Quality Labels

| label | samples |
|---|---:|
| `no_strong_support` | 7 |
| `fallback_positive_only` | 4 |
| `positive_but_status_conflicted` | 4 |
| `partial_supported_positive` | 1 |

## 3. Key Group Comparison

### false_flip_reject

| label | samples |
|---|---:|
| `fallback_positive_only` | 1 |

### oracle_recovered_accept

| label | samples |
|---|---:|
| `partial_supported_positive` | 1 |
| `positive_but_status_conflicted` | 1 |

### other

| label | samples |
|---|---:|
| `no_strong_support` | 7 |
| `fallback_positive_only` | 3 |
| `positive_but_status_conflicted` | 3 |

## 4. Interpretation

- If oracle-recovered accept cases have real strong support but final decision still blocks them, the next fix is support accounting / claim-status reconciliation.
- If false-flip reject cases also look positive under the same support accounting, runtime accept relaxation is unsafe.
- If most strong support is fallback/meta/unsupported-bound, the next fix is evidence-to-claim grounding rather than final decision thresholds.

## 5. Main Finding

The positive side of ReviewState is not clean enough for final decision:

- There are `14` strong positive evidence items, but only `1` is attached to a supported/partially-supported claim.
- `7` strong positive evidence items are attached to claims still marked `unsupported`.
- `6` strong positive evidence items are attached to fallback claims.
- `12/16` samples still hit `strong<2`.

This explains why negative cleanup alone fails. The final decision layer cannot safely recover accept because positive support is either missing, fallback-bound, or status-conflicted. The false-flip reject `aTBE70xiFw` has two strong positives, but both are fallback-bound; any rule that treats raw strong count as accept evidence will incorrectly flip it.

## 6. Next Direction

The next runtime candidate should not be decision-threshold relaxation. It should be a minimal **Support Grounding / Claim-Status Reconciliation** design, but only after another offline simulation verifies this rule:

- Count strong support for final decision only if it is attached to a non-fallback claim.
- If a non-fallback claim has strong support and no strong contradiction, reconcile its status away from `unsupported`.
- Do not count fallback-bound support as accept evidence.

This rule should recover `KI9NqjLVDT` or `QAAsnSRwgu` while keeping `aTBE70xiFw` rejected.

