# Claim Status / Support Consistency Audit

**运行行为是否改变**：否。

## 1. 状态冲突总计

| metric | count |
|---|---|
| status_partially_supported_with_no_support_count | 11 |
| status_support_not_reflected_in_claim_status_count | 33 |
| status_unsupported_with_2plus_strong_support_count | 7 |
| status_unsupported_with_strong_support_count | 33 |

## 2. Claim-level case table

| run | paper_id | gold | claim_id | claim_status | strong_support_ids | strong_contradiction_ids | support_count | contradiction_count | status_guard | evidence_gap_same_claim |
|---|---|---|---|---|---|---|---|---|---|---|
| 4b_focus | hj323oR3rw | accept | claim-fallback-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_focus | QAAsnSRwgu | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_focus | QAAsnSRwgu | accept | claim-3 | supported | evidence-3 |  | 1 | 0 | False | True |
| 4b_focus | gzqrANCF4g | accept | claim-3 | unsupported | evidence-3 |  | 1 | 0 | False | True |
| 4b_focus | KI9NqjLVDT | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_focus | KI9NqjLVDT | accept | claim-2 | unsupported | evidence-2 |  | 1 | 0 | False | True |
| 4b_focus | KI9NqjLVDT | accept | claim-3 | unsupported | evidence-3 |  | 1 | 0 | False | True |
| 4b_focus | BXY6fe7q31 | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_focus | TPAj63ax4Y | reject | claim-fallback-1 | unsupported | evidence-1,evidence-2 |  | 2 | 0 | False | True |
| 4b_focus | aTBE70xiFw | reject | claim-fallback-1 | unsupported | evidence-1,evidence-2 |  | 2 | 0 | False | True |
| 4b_focus | GE6iywJtsV | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_focus | KOUAayk5Kx | reject | claim-fallback-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_mixed_v2 | xYzOkOGD96 | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 4b_mixed_v2 | GSckuQMzBG | reject | claim-fallback-1 | unsupported | evidence-1,evidence-2 |  | 2 | 0 | False | True |
| 4b_mixed_v2 | IdAyXxBud7 | accept | claim-fallback-1 | supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | WNxlJJIEVj | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | uOrfve3prk | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | uOrfve3prk | reject | claim-2 | unsupported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | hj323oR3rw | accept | claim-1 | unsupported | evidence-2,evidence-3 |  | 2 | 0 | False | True |
| 9b_fulltest_mainline | 9zEBK3E9bX | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | QAAsnSRwgu | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | QAAsnSRwgu | accept | claim-2 | unsupported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | X41c4uB4k0 | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | X41c4uB4k0 | accept | claim-2 | unsupported | evidence-2,evidence-the-paper-claims-that-existing-m |  | 2 | 0 | False | True |
| 9b_fulltest_mainline | NnExMNiTHw | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | NnExMNiTHw | reject | claim-2 | supported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | fGXyvmWpw6 | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | fGXyvmWpw6 | reject | claim-2 | unsupported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | BXY6fe7q31 | accept | claim-2 | supported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | TPAj63ax4Y | reject | claim-1 | unsupported | evidence-1,evidence-2,evidence-3 |  | 3 | 0 | False | True |
| 9b_fulltest_mainline | mHv6wcBb0z | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | xUe1YqEgd6 | reject | claim-1 | unsupported | evidence-1,evidence-2 |  | 2 | 0 | False | True |
| 9b_fulltest_mainline | jVEoydFOl9 | accept | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | YXn76HMetm | reject | claim-1 | supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | KOUAayk5Kx | reject | claim-1 | partially_supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | ZHr0JajZfH | reject | claim-1 | supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | rEqETC88RY | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | aTBE70xiFw | reject | claim-1 | partially_supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | aTBE70xiFw | reject | claim-2 | supported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | kam84eEmub | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | kam84eEmub | reject | claim-2 | unsupported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | kam84eEmub | reject | claim-3 | supported | evidence-3 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | 2L7KQ4qbHi | reject | claim-1 | unsupported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | aRxLDcxFcL | reject | claim-1 | supported | evidence-1 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | aRxLDcxFcL | reject | claim-2 | supported | evidence-2 |  | 1 | 0 | False | True |
| 9b_fulltest_mainline | aRxLDcxFcL | reject | claim-3 | supported | evidence-3 |  | 1 | 0 | False | True |

## 3. 判断

- **claim-status reconciliation** 是后续必要 hygiene，但只有在 real-claim strong support 已稳定形成后才适合作为第一实现。
- 若 strong support 总量不足，先改 status 同步无法恢复 accept。
