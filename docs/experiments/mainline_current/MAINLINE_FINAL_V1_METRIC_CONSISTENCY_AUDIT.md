# Mainline-Final-v1 Metric Consistency Audit

## 结论

`fallback_strong_support_total=13` 是 raw ReviewState 中的 fallback-bound strong support 残留，主要绑定到 `claim-fallback-1`，多数来源是 abstract。它不应被解释为 decision-eligible real-claim strong support。

## Aggregate

| metric | value |
| --- | ---: |
| raw_fallback_strong_total | 13 |
| rows_with_raw_fallback_strong | 7 |
| accept_like_rows_with_raw_fallback_strong | 0 |

## Fallback Source Counts

| source | count |
| --- | ---: |
| abstract | 13 |

## Affected Rows

| paper_id | gold | runtime_final | raw_fallback_strong | decision_real_strong | recommendation_view |
| --- | --- | --- | ---: | ---: | --- |
| uOrfve3prk | reject | reject | 3 | 0 | not_assessable |
| GE6iywJtsV | reject | reject | 1 | 0 | not_assessable |
| QAAsnSRwgu | accept | reject | 1 | 0 | not_assessable |
| cklg91aPGk | reject | reject | 3 | 0 | not_assessable |
| xUe1YqEgd6 | reject | reject | 2 | 0 | not_assessable |
| 9JRsAj3ymy | reject | reject | 2 | 0 | not_assessable |
| rEqETC88RY | reject | reject | 1 | 0 | not_assessable |
