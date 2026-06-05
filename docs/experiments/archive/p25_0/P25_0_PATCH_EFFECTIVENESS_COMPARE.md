# P25.0 Patch Effectiveness Compare

## Recovery-Relevant Failure Codes (attempt-level)
| Failure Code | 4B | 9B |
| --- | ---: | ---: |
| BLOCKED_BY_POLICY | 6 | 17 |
| INSUFFICIENT_EVIDENCE | 1 | 2 |
| NO_EFFECT_PATCH | 8 | 1 |
| SUCCESS | 4 | 5 |
| UNRESOLVED_CONFLICT | 0 | 1 |

## Rates Among Emitted Recovery Patches
| Metric | 4B | 9B |
| --- | ---: | ---: |
| success_rate_among_emitted | 0.2353 | 0.2778 |
| no_effect_rate_among_emitted | 0.4706 | 0.0556 |
| blocked_rate_among_emitted | 0.2353 | 0.5 |

## Emitted / Validated / Committed Turns
| Metric | 4B | 9B |
| --- | ---: | ---: |
| emitted_turns | 17 | 18 |
| validated_turns | 19 | 26 |
| committed_turns | 4 | 5 |
