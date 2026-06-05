# Negative Evidence Formation v2 Rule Simulation

## Group Summary

| group | rows | v1_2_trusted_rows | v2_trusted_rows | parse_error_rows |
| --- | ---: | ---: | ---: | ---: |
| false_accept | 7 | 5 | 2 | 0 |
| recovered_accept | 3 | 1 | 0 | 0 |

## Label Counts

| label | count |
| --- | ---: |
| weak_candidate_anchor_insufficient | 3 |
| v2_trusted_blocker | 3 |
| not_assessable_context_limited | 2 |

## Case Table

| paper_id | gold | tag | v1_2 | v2 | labels |
| --- | --- | --- | ---: | ---: | --- |
| NnExMNiTHw | reject | false_accept | 0 | 0 |  |
| WLgbjzKJkk | reject | false_accept | 1 | 0 | weak_candidate_anchor_insufficient:1 |
| WpXq5n8yLb | reject | false_accept | 2 | 0 | not_assessable_context_limited:1, weak_candidate_anchor_insufficient:1 |
| a6SntIisgg | reject | false_accept | 0 | 0 |  |
| aTBE70xiFw | reject | false_accept | 1 | 1 | v2_trusted_blocker:1 |
| kam84eEmub | reject | false_accept | 2 | 2 | v2_trusted_blocker:2 |
| ye3NrNrYOY | reject | false_accept | 1 | 0 | weak_candidate_anchor_insufficient:1 |
| 1HCN4pjTb4 | accept | recovered_accept | 0 | 0 |  |
| BXY6fe7q31 | accept | recovered_accept | 0 | 0 |  |
| KI9NqjLVDT | accept | recovered_accept | 1 | 0 | not_assessable_context_limited:1 |
