# Negative Evidence Formation Pass v1.3 Precision Audit

## Summary

| group | rows | strict_trusted_blocker_rows | demoted_context_limited_rows | parse_error_rows |
| --- | ---: | ---: | ---: | ---: |
| false_accept | 7 | 2 | 4 | 0 |
| recovered_accept | 3 | 0 | 1 | 0 |

## Case Table

| paper_id | gold | tag | v1_2_trusted | strict_trusted | demoted_context_limited |
| --- | --- | --- | ---: | ---: | ---: |
| NnExMNiTHw | reject | false_accept | 0 | 0 | 0 |
| WLgbjzKJkk | reject | false_accept | 1 | 0 | 1 |
| WpXq5n8yLb | reject | false_accept | 2 | 0 | 2 |
| a6SntIisgg | reject | false_accept | 0 | 0 | 0 |
| aTBE70xiFw | reject | false_accept | 1 | 1 | 0 |
| kam84eEmub | reject | false_accept | 2 | 1 | 1 |
| ye3NrNrYOY | reject | false_accept | 1 | 0 | 1 |
| 1HCN4pjTb4 | accept | recovered_accept | 0 | 0 | 0 |
| BXY6fe7q31 | accept | recovered_accept | 0 | 0 | 0 |
| KI9NqjLVDT | accept | recovered_accept | 1 | 0 | 1 |

## Decision

v1.2 的主要风险是把 `abstract/context 看不到结果` 当成 paper-grounded negative blocker。v1.3 严格过滤后，只有非 abstract 的 experiment/result/table/figure/metric anchor 才能作为 trusted blocker。若 strict trusted blocker 过低，下一步应先改 negative evidence context，而不是把 blocker 接入 final decision。
