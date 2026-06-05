# Evidence JSON Contract v1 Fulltest39 对比

| 指标 | Retained baseline | JSON Contract v1 |
| --- | ---: | ---: |
| rows | 39 | 39 |
| avg_reward | 0.5047452333165214 | 0.5024626689383527 |
| accuracy | 0.7692307692307693 | 0.7692307692307693 |
| macro_f1 | 0.4347826086956522 | 0.4347826086956522 |
| accept_recall | 0.0 | 0.0 |
| reject_recall | 1.0 | 1.0 |
| predicted_accept_count | 0 | 0 |
| evidence_worker_calls | 87 | 188 |
| evidence_parse_errors | 23 | 33 |
| evidence_fallback_payloads | 22 | 2 |
| turn_log_evidence_json_status_rows | 0 | 188 |
| turn_status_json_valid | 0 | 154 |
| real_strong | 10 | 13 |
| nonabs_strong | 5 | 10 |
| empirical_strong | 8 | 13 |
| fallback_strong | 0 | 0 |
| invalid_bound_evidence | 0 | 4 |
| fallback_extraction_evidence | 17 | 2 |
| unresolved_total | 209 | 234 |
| gaps_total | 155 | 137 |
| candidate_flaws_total | 58 | 45 |

## 结论

JSON Contract v1 在 fulltest39 上保留。它把 Evidence fallback payload 控制在很低水平，同时保持 fallback strong support 为 0，并提高 real/non-abstract/empirical strong support。final decision 仍然 all-reject，这不是本轮失败，而是后续 final-view hygiene / criterion-grounded decision simulation 要处理的问题。
