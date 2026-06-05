# HARD_NEGATIVE_CASE_TABLE_V1

这张表用于解释哪些 high-support reject 不能被裸 support 规则接收，以及哪些 accept 样本需要避免被负面噪声误压。

| paper_id | gold | view | bucket | real | nonabs | empirical | indep | hard_negative_status | first_blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jVEoydFOl9 | accept | accept_like | accept_protect_cases | 4 | 4 | 3 | 4 | context_limited_no_grounded_blocker | none |
| KI9NqjLVDT | accept | borderline_positive | accept_protect_cases | 3 | 3 | 3 | 3 | unverified_blocker_candidate | open_missing_claim_support |
| BXY6fe7q31 | accept | borderline_insufficient | accept_protect_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| QAAsnSRwgu | accept | borderline_insufficient | accept_protect_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| X41c4uB4k0 | accept | borderline_insufficient | accept_protect_cases | 1 | 1 | 0 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| WNxlJJIEVj | reject | borderline_insufficient | background_cases | 1 | 1 | 0 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| aRxLDcxFcL | reject | borderline_insufficient | background_cases | 1 | 1 | 0 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| fGXyvmWpw6 | reject | borderline_insufficient | background_cases | 1 | 1 | 0 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| gzqrANCF4g | accept | reject_like | background_cases | 1 | 1 | 1 | 1 | grounded_blocker_found | grounded_major_or_critical_flaw |
| 1HCN4pjTb4 | accept | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| 2L7KQ4qbHi | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| 9JRsAj3ymy | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| GE6iywJtsV | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| HPuLU6q7xq | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| LebzzClHYw | accept | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| XH3OiIhtvf | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| ZHr0JajZfH | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| hj323oR3rw | accept | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| kam84eEmub | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| rEqETC88RY | reject | not_assessable_uncertain | background_cases | 0 | 0 | 0 | 0 | unverified_blocker_candidate | open_missing_claim_support |
| 9zEBK3E9bX | reject | borderline_positive | false_accept_risk_reject_cases | 3 | 3 | 3 | 3 | unverified_blocker_candidate | open_missing_claim_support |
| KOUAayk5Kx | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_unanchored_gap |
| LieTse3fQB | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| NnExMNiTHw | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| QAgwFiIY4p | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 1 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| TPAj63ax4Y | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 1 | unverified_blocker_candidate | open_unanchored_gap |
| WLgbjzKJkk | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 1 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| WpXq5n8yLb | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| XyB4VvF01X | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| YXn76HMetm | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| a6SntIisgg | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 0 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| cklg91aPGk | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 2 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| uOrfve3prk | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 1 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| xUe1YqEgd6 | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 1 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| ye3NrNrYOY | reject | borderline_insufficient | false_accept_risk_reject_cases | 2 | 2 | 1 | 2 | unverified_blocker_candidate | open_missing_claim_support |
| 7Dub7UXTXN | reject | borderline_insufficient | false_accept_risk_reject_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| N0isTh3rml | reject | borderline_insufficient | false_accept_risk_reject_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| aTBE70xiFw | reject | borderline_insufficient | false_accept_risk_reject_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | open_missing_claim_support |
| mHv6wcBb0z | reject | borderline_insufficient | false_accept_risk_reject_cases | 1 | 1 | 1 | 1 | unverified_blocker_candidate | paper_grounded_open_conflict |
