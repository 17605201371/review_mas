# HARD_NEGATIVE_CASE_STUDY_V1

## 结论

本轮只做离线 case study，不改 runtime。结果显示：高正向支持的 reject 样本大量存在，但多数样本只有未验证 blocker 或 context/meta burden，缺少稳定 paper-grounded hard-negative blocker。因此 borderline_positive 不能直接映射为 accept。

## Aggregate

| metric | value |
| --- | --- |
| rows | 39 |
| gold_counts | {'reject': 30, 'accept': 9} |
| recommendation_view_counts | {'borderline_insufficient': 24, 'not_assessable_uncertain': 11, 'borderline_positive': 2, 'reject_like': 1, 'accept_like': 1} |
| hard_negative_status_counts | {'unverified_blocker_candidate': 37, 'grounded_blocker_found': 1, 'context_limited_no_grounded_blocker': 1} |
| bucket_counts | {'false_accept_risk_reject_cases': 19, 'background_cases': 15, 'accept_protect_cases': 5} |

## False-Accept Risk Reject Cases

这些样本有 real/non-abstract/empirical support，但 gold 是 reject。它们是 final recommendation 不能激进放松的主要原因。

| paper_id | view | real | empirical | status | blocker_candidates |
| --- | --- | --- | --- | --- | --- |
| ye3NrNrYOY | borderline_insufficient | 2 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| uOrfve3prk | borderline_insufficient | 2 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| 7Dub7UXTXN | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| 9zEBK3E9bX | borderline_positive | 3 | 3 | unverified_blocker_candidate | open_missing_claim_support |
| XyB4VvF01X | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support; open_unanchored_gap |
| WpXq5n8yLb | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| NnExMNiTHw | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support; open_missing_claim_support |
| a6SntIisgg | borderline_insufficient | 2 | 0 | unverified_blocker_candidate | open_missing_claim_support; open_missing_claim_support; open_unanchored_gap |
| cklg91aPGk | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| QAgwFiIY4p | borderline_insufficient | 2 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| TPAj63ax4Y | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_unanchored_gap |
| mHv6wcBb0z | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | paper_grounded_open_conflict |
| xUe1YqEgd6 | borderline_insufficient | 2 | 1 | unverified_blocker_candidate | open_missing_claim_support; open_missing_claim_support |
| YXn76HMetm | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| KOUAayk5Kx | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_unanchored_gap |
| WLgbjzKJkk | borderline_insufficient | 2 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| aTBE70xiFw | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| LieTse3fQB | borderline_insufficient | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| N0isTh3rml | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |

## Accept-Protect Cases

这些样本是 gold accept，下一轮 policy 不能因为 stale gap / meta unresolved / fallback burden 把它们继续压成 reject。

| paper_id | view | real | empirical | status | blocker_candidates |
| --- | --- | --- | --- | --- | --- |
| QAAsnSRwgu | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support; open_missing_claim_support |
| X41c4uB4k0 | borderline_insufficient | 1 | 0 | unverified_blocker_candidate | open_missing_claim_support; open_missing_claim_support |
| KI9NqjLVDT | borderline_positive | 3 | 3 | unverified_blocker_candidate | open_missing_claim_support |
| BXY6fe7q31 | borderline_insufficient | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| jVEoydFOl9 | accept_like | 4 | 3 | context_limited_no_grounded_blocker | none |
