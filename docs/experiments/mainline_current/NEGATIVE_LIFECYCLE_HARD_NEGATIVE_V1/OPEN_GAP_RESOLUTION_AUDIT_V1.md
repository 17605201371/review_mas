# OPEN_GAP_RESOLUTION_AUDIT_V1

## 结论

这份审计只看 final-view hygiene 后仍保留的 open evidence gaps。目标是判断剩余 gap 是真正缺 evidence，还是 evidence/claim 关联或 claim status 的问题。

## Aggregate

| metric | value |
| --- | --- |
| rows | 39 |
| open_gap_total | 52 |

## Gap Categories

| category | count |
| --- | --- |
| claim_has_no_support | 22 |
| claim_has_only_weak_or_unusable_support | 30 |

## High-gap Cases

| paper_id | gold | open_gap_count | gap_categories |
| --- | --- | --- | --- |
| ZHr0JajZfH | reject | 4 | {'claim_has_only_weak_or_unusable_support': 2, 'claim_has_no_support': 2} |
| hj323oR3rw | accept | 3 | {'claim_has_only_weak_or_unusable_support': 3} |
| 9JRsAj3ymy | reject | 3 | {'claim_has_only_weak_or_unusable_support': 2, 'claim_has_no_support': 1} |
| rEqETC88RY | reject | 3 | {'claim_has_only_weak_or_unusable_support': 3} |
| WNxlJJIEVj | reject | 2 | {'claim_has_only_weak_or_unusable_support': 2} |
| QAAsnSRwgu | accept | 2 | {'claim_has_only_weak_or_unusable_support': 1, 'claim_has_no_support': 1} |
| X41c4uB4k0 | accept | 2 | {'claim_has_only_weak_or_unusable_support': 1, 'claim_has_no_support': 1} |
| NnExMNiTHw | reject | 2 | {'claim_has_only_weak_or_unusable_support': 1, 'claim_has_no_support': 1} |
| a6SntIisgg | reject | 2 | {'claim_has_no_support': 2} |
| LebzzClHYw | accept | 2 | {'claim_has_only_weak_or_unusable_support': 2} |
| xUe1YqEgd6 | reject | 2 | {'claim_has_no_support': 2} |
| aRxLDcxFcL | reject | 2 | {'claim_has_only_weak_or_unusable_support': 1, 'claim_has_no_support': 1} |
| ye3NrNrYOY | reject | 1 | {'claim_has_no_support': 1} |
| uOrfve3prk | reject | 1 | {'claim_has_no_support': 1} |
| 7Dub7UXTXN | reject | 1 | {'claim_has_only_weak_or_unusable_support': 1} |

## Decision

- `claim_has_no_support` 表示 Evidence Agent 确实没有为该 claim 形成 support，优先回到 evidence/context 或 target selection。
- `claim_has_only_weak_or_unusable_support` 表示 support 有但质量不足，不应直接 accept。
- `claim_status_overstates_support` 或 `claim_support_ids_missing_from_evidence_map` 表示 state consistency / merge 还有修复空间。
- 这轮不建议把 open gap 直接作为 reject blocker；它更适合作为 `not_assessable` 或 `borderline_insufficient` 的解释字段。
