# P25.1 Patch Effectiveness

## 9B Expanded Recovery-Relevant Failure Codes (attempt-level)
| Failure Code | 9B main |
| --- | ---: |
| BLOCKED_BY_POLICY | 40 |
| INVALID_STATUS_TRANSITION | 2 |
| NO_EFFECT_PATCH | 3 |
| SUCCESS | 7 |
| UNRESOLVED_CONFLICT | 1 |

## 9B Expanded Rates Among Emitted Recovery Patches
| Metric | 9B main |
| --- | ---: |
| success_rate_among_emitted | 0.2917 |
| no_effect_rate_among_emitted | 0.125 |
| blocked_rate_among_emitted | 0.4583 |

## Fixed Reference Compare (4B vs 9B)
| Failure Code | 4B reference | 9B reference |
| --- | ---: | ---: |
| BLOCKED_BY_POLICY | 13 | 17 |
| INSUFFICIENT_EVIDENCE | 1 | 0 |
| NO_EFFECT_PATCH | 12 | 3 |
| SUCCESS | 2 | 4 |

## Fixed Reference Rates Among Emitted Recovery Patches
| Metric | 4B reference | 9B reference |
| --- | ---: | ---: |
| success_rate_among_emitted | 0.1 | 0.3077 |
| no_effect_rate_among_emitted | 0.6 | 0.2308 |
| blocked_rate_among_emitted | 0.25 | 0.4615 |
