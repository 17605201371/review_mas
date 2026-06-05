# Negative Evidence Formation Pass v1 Compare

## Summary

| group | rows | trusted_blocker_rows | avg_trusted_blockers | not_assessable_rows | parse_error_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| false_accept | 7 | 1 | 0.143 | 7 | 3 |
| recovered_accept | 3 | 0 | 0.0 | 3 | 2 |

## Interpretation

- false accept 中形成 trusted blocker，说明负证据 formation pass 有潜在价值。
- recovered accept 中形成 trusted blocker，则说明规则还不够区分，不能直接进入 final decision。
- parse_error_rows 应保持低，否则该 pass 还需要 JSON robustness。
