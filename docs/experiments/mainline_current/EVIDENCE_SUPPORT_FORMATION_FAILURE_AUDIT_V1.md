# Evidence Support Formation Failure Audit v1

## 结论

v1.1 已经把 fallback target 污染压下去，但 fulltest39 仍无法形成 2+ real strong support。离线审计显示，主要问题不是 final decision 阈值，而是 Evidence Agent 的 strong support 形成本身不足；多数样本在 payload 阶段就没有 2 条 real strong support。

## 汇总

- `rows`: 39
- `extraction_failure_no_payload_strong_real`: 22
- `single_support_only`: 3
- `merge_or_retention_loss`: 10
- `has_2plus_final_strong`: 0
- `payload_strong_real_total`: 33
- `final_strong_real_total`: 9
- `payload_nonabstract_total`: 22
- `final_nonabstract_total`: 9
- `payload_empirical_total`: 18
- `final_empirical_total`: 9
- `rows_payload_strong_gt_final`: 14
- `rows_final_evidence_map_at_12plus`: 0

## 解释

- `extraction_failure_no_payload_strong_real` 表示 Evidence Agent 输出阶段就没有 real-claim strong support。
- `single_support_only` 表示最终 state 只有 1 条 real-claim strong support，无法支撑 2+ independent support。
- `merge_or_retention_loss` 表示 payload 中已有 2+ real strong support，但最终 state 少于 2，下一步才需要看 merge/retention。

当前结果显示，优先级应是 Evidence extraction / support quality，而不是 final decision、controller 或 fallback target 继续微调。

## Case Table

| paper_id | category | payload strong real | final strong real | payload nonabs | final nonabs | payload empirical | final empirical | final evidence total |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ye3NrNrYOY | merge_or_retention_loss | 2 | 0 | 1 | 0 | 0 | 0 | 3 |
| WNxlJJIEVj | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| uOrfve3prk | single_support_only | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| hj323oR3rw | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| 7Dub7UXTXN | merge_or_retention_loss | 3 | 0 | 0 | 0 | 0 | 0 | 3 |
| 9zEBK3E9bX | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| XyB4VvF01X | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| GE6iywJtsV | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| QAAsnSRwgu | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| WpXq5n8yLb | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| X41c4uB4k0 | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| NnExMNiTHw | single_support_only | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| gzqrANCF4g | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| a6SntIisgg | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| cklg91aPGk | merge_or_retention_loss | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| HPuLU6q7xq | merge_or_retention_loss | 3 | 1 | 3 | 1 | 3 | 1 | 2 |
| fGXyvmWpw6 | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| QAgwFiIY4p | single_support_only | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| KI9NqjLVDT | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| 1HCN4pjTb4 | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| LebzzClHYw | other_low_support | 1 | 0 | 1 | 0 | 0 | 0 | 2 |
| BXY6fe7q31 | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| TPAj63ax4Y | merge_or_retention_loss | 2 | 1 | 2 | 1 | 1 | 1 | 3 |
| mHv6wcBb0z | merge_or_retention_loss | 2 | 1 | 2 | 1 | 2 | 1 | 2 |
| xUe1YqEgd6 | other_low_support | 1 | 0 | 1 | 0 | 1 | 0 | 2 |
| jVEoydFOl9 | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| YXn76HMetm | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| KOUAayk5Kx | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| XH3OiIhtvf | merge_or_retention_loss | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| ZHr0JajZfH | merge_or_retention_loss | 3 | 1 | 2 | 1 | 2 | 1 | 2 |
| WLgbjzKJkk | other_low_support | 1 | 0 | 1 | 0 | 0 | 0 | 2 |
| 9JRsAj3ymy | other_low_support | 1 | 0 | 1 | 0 | 1 | 0 | 2 |
| rEqETC88RY | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| aTBE70xiFw | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| LieTse3fQB | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| kam84eEmub | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| N0isTh3rml | merge_or_retention_loss | 4 | 0 | 0 | 0 | 0 | 0 | 4 |
| 2L7KQ4qbHi | extraction_failure_no_payload_strong_real | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| aRxLDcxFcL | merge_or_retention_loss | 3 | 1 | 3 | 1 | 3 | 1 | 2 |

## 下一步

下一刀不应继续做 target isolation，也不应调整 accept/reject。应检查 Evidence Agent 为什么 payload 阶段多数样本没有产生 2+ real strong support：重点看 claim selection、section context 与 evidence output schema 对 non-abstract / empirical / independent support 的约束。
