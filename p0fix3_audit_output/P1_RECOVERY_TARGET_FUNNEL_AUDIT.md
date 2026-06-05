# P1-1: Recovery Funnel Audit

## Summary
- recovery_attempted: 11
- validated: 3
- committed: 2
- effective_repair: 1
- safe_resolution: 0
- failure_codes: {'BLOCKED_BY_POLICY': 8, 'SUCCESS': 2, 'INSUFFICIENT_EVIDENCE': 1}
- target_gates: {'weak_target': 8, 'real_target': 2, 'fallback_target': 1}

## Turn Details

| paper_id | turn | target | gate | failure_code | validated | committed | effective | safe | operation |
|---|---|---|---|---|---|---|---|---|---|
| 9zEBK3E9bX | 4 | claim-2 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| QAAsnSRwgu | 4 | flaw-negativ | real_target | SUCCESS | True | True | True | False | route_to_assessment_limitation |
| QAAsnSRwgu | 5 | flaw-negativ | real_target | SUCCESS | True | True | False | False | route_to_assessment_limitation |
| WLgbjzKJkk | 4 | claim-2 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| WNxlJJIEVj | 4 | claim-2 | weak_target | INSUFFICIENT_EVIDENCE | True | False | False | False | reject_patch |
| WNxlJJIEVj | 6 | claim-2 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| X41c4uB4k0 | 6 | claim-contex | fallback_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| ZHr0JajZfH | 4 | claim-2 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| hj323oR3rw | 4 | claim-1 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| hj323oR3rw | 5 | claim-1 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
| kam84eEmub | 4 | claim-1 | weak_target | BLOCKED_BY_POLICY | False | False | False | False | reject_patch |
