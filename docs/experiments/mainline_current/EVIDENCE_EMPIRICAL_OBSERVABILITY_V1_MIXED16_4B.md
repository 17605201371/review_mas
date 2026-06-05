# Evidence Empirical Observability v1 Mixed16 4B

## 结论

- rows: `16`
- evidence_turns: `83`
- field_turns: `67`
- final_decision_counts: `{'reject': 16}`
- avg_reward: `0.4338`
- structuring_status_counts: `{'empirical_payload_without_strong_support': 20, 'strong_empirical_payload_formed': 7, 'no_raw_empirical_signal': 13, 'raw_empirical_no_payload_evidence': 19, 'raw_empirical_payload_no_empirical_evidence': 8}`
- raw_empirical_term_total: `239`
- payload_empirical_evidence_total: `33`
- payload_strong_empirical_total: `8`
- rows_with_payload_empirical: `14`
- rows_with_strong_empirical: `6`

当前主判断：**empirical evidence is visible/structured but strength calibration is the bottleneck**。

## 状态分布

| status | count | rate |
| --- | ---: | ---: |
| empirical_payload_without_strong_support | 20 | 0.299 |
| raw_empirical_no_payload_evidence | 19 | 0.284 |
| no_raw_empirical_signal | 13 | 0.194 |
| raw_empirical_payload_no_empirical_evidence | 8 | 0.119 |
| strong_empirical_payload_formed | 7 | 0.104 |

## Case Table

| paper_id | pred | reward | evidence_turns | raw_emp_terms | payload_emp | strong_emp | status_counts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| cWEfRkYj46 | reject | 0.3987 | 7 | 11 | 2 | 1 | {'empirical_payload_without_strong_support': 1, 'strong_empirical_payload_formed': 1, 'no_raw_empirical_signal': 3, 'raw_empirical_no_payload_evidence': 1} |
| xYzOkOGD96 | reject | 0.7435 | 6 | 29 | 3 | 0 | {'empirical_payload_without_strong_support': 2, 'raw_empirical_payload_no_empirical_evidence': 1, 'raw_empirical_no_payload_evidence': 2} |
| nrvoWOWcyg | reject | 0.2035 | 3 | 11 | 1 | 0 | {'raw_empirical_payload_no_empirical_evidence': 1, 'empirical_payload_without_strong_support': 1} |
| bcHty5VvkQ | reject | 0.5093 | 4 | 19 | 5 | 0 | {'empirical_payload_without_strong_support': 3} |
| VEJzjAvaIy | reject | 0.3283 | 7 | 14 | 2 | 2 | {'strong_empirical_payload_formed': 2, 'raw_empirical_no_payload_evidence': 4} |
| k243qi7S50 | reject | 0.6076 | 7 | 12 | 3 | 0 | {'empirical_payload_without_strong_support': 2, 'no_raw_empirical_signal': 3, 'raw_empirical_no_payload_evidence': 1} |
| nrRkAAAufl | reject | 0.2641 | 6 | 37 | 3 | 0 | {'empirical_payload_without_strong_support': 3, 'no_raw_empirical_signal': 1, 'raw_empirical_no_payload_evidence': 1} |
| GSckuQMzBG | reject | 0.5044 | 7 | 17 | 2 | 1 | {'empirical_payload_without_strong_support': 1, 'strong_empirical_payload_formed': 1, 'no_raw_empirical_signal': 1, 'raw_empirical_no_payload_evidence': 3} |
| IdAyXxBud7 | reject | 0.2271 | 3 | 9 | 2 | 0 | {'empirical_payload_without_strong_support': 2} |
| JdWpIe70FL | reject | 0.5718 | 5 | 34 | 5 | 2 | {'strong_empirical_payload_formed': 1, 'empirical_payload_without_strong_support': 2, 'raw_empirical_no_payload_evidence': 1} |
| pOq9vDIYev | reject | 0.2583 | 7 | 23 | 1 | 1 | {'raw_empirical_payload_no_empirical_evidence': 1, 'strong_empirical_payload_formed': 1, 'raw_empirical_no_payload_evidence': 4} |
| YvWuac63bg | reject | 0.6204 | 3 | 6 | 2 | 0 | {'empirical_payload_without_strong_support': 2} |
| giU9fYGTND | reject | 0.2587 | 2 | 5 | 1 | 1 | {'strong_empirical_payload_formed': 1} |
| qgyF6JVmar | reject | 0.6678 | 4 | 4 | 0 | 0 | {'raw_empirical_payload_no_empirical_evidence': 3} |
| cpGPPLLYYx | reject | 0.2792 | 7 | 1 | 1 | 0 | {'no_raw_empirical_signal': 5, 'empirical_payload_without_strong_support': 1} |
| 77plFC53J5 | reject | 0.4987 | 5 | 7 | 0 | 0 | {'raw_empirical_payload_no_empirical_evidence': 2, 'raw_empirical_no_payload_evidence': 2} |

## 下一步

- 这轮仍然不应该调 final decision，也不应该回到 sticky/throttle。
- 如果主判断是 context visibility，则下一刀应是 empirical/result/table-aware evidence context selection。
- 如果主判断是 strength calibration，则下一刀应是 Evidence Agent empirical structuring / strength calibration。
- 如果 strong empirical 已稳定形成，再讨论 final recommendation policy。
