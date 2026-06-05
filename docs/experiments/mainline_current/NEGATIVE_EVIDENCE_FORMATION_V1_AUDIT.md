# Negative Evidence Formation / Flaw Confirmation v1 Audit

## 结论

当前 9B dry-run 的 false accept 不是 positive support 太多这么简单，而是系统缺少能与人工 hard weakness 对齐的可信负向 blocker。系统侧多数负向信号仍停留在 weak candidate / unresolved / meta burden，不能安全用于 final decision。

## Group Summary

| group | rows | trusted_blocker_rows | weak_candidate_rows | oracle_core_hard_rows | formation_gap_rows | avg_real_strong | avg_weak_candidates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| false_accept | 7 | 0 | 5 | 7 | 7 | 2.714 | 0.714 |
| recovered_accept | 3 | 1 | 1 | 3 | 2 | 2.333 | 0.333 |
| false_reject_or_unrecovered_accept | 6 | 2 | 3 | 5 | 3 | 0.667 | 0.5 |
| other | 23 | 3 | 11 | 21 | 18 | 0.304 | 0.826 |

## Criterion Gap

| criterion | formation_gap_count |
| --- | ---: |
| unspecified | 28 |
| empirical | 26 |
| clarity | 25 |
| soundness | 23 |
| significance | 16 |
| novelty | 13 |

## 解释

- `trusted_blocker_rows` 很低，说明系统目前缺少 paper-grounded negative evidence / confirmed flaw。
- `weak_candidate_rows` 高，说明系统不是完全看不到负面线索，而是缺少确认、绑定和 criterion linkage。
- reviewer comments 只作为离线 oracle-style 参照；它不能直接变成 reject rule，因为 recovered accept 中也存在 hard weakness comments。
