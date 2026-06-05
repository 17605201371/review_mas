# Evidence ID Turn-Scoping v1 Fulltest39 Compare

## 对照对象

本文件对比 `Evidence JSON Contract v1` 与 `Evidence ID Turn-Scoping v1` 在 4B fulltest39 上的结果。

## 核心指标

| 指标 | json_contract_v1 | id_turn_scoping_v1 |
|---|---|---|
| 样本数 | 39 | 39 |
| avg_reward | 0.502463 | 0.491294 |
| accuracy | 0.769231 | 0.74359 |
| accept_recall | 0 | 0 |
| reject_recall | 1 | 0.966667 |
| macro_f1 | 0.434783 | 0.426471 |
| pred_accept_count | 0 | 1 |
| false_accept_ids | [] | ['cklg91aPGk'] |
| payload_evidence_total | 161 | 146 |
| payload_unique_total | 75 | 142 |
| rows_payload_dup | 33 | 2 |
| final_evidence_total | 75 | 142 |
| final_real_strong | 13 | 14 |
| rows_final_2plus_real | 1 | 4 |
| accept_final_real_strong | 2 | 3 |
| accept_rows_final_2plus_real | 0 | 1 |
| accept_payload_real_strong | 12 | 9 |
| accept_rows_payload_2plus_real | 4 | 3 |
| invalid_bound | 4 | 23 |
| invalid_unbound | 0 | 0 |
| original_claim_id_records | 0 | 0 |
| unresolved_total | 234 | 196 |
| gaps_total | 137 | 134 |
| candidate_flaws_total | 45 | 49 |

## 结论

`Evidence ID Turn-Scoping v1` 命中了一个明确的 live-state 合并 bug：Evidence Agent 多轮复用 `evidence-1` / `evidence-2`，导致后续证据覆盖前序证据。fulltest39 中，payload 重复样本数从 `33` 降到 `2`，final evidence 总数从 `75` 增到 `142`，final 2+ real strong support 样本数从 `1` 增到 `4`。

副作用也很清楚：由于更多证据被保留下来，invalid claim binding 暴露得更多，`invalid_bound` 从 `4` 升到 `23`。这不是 turn-scoping 本身的反证，而是它修复 evidence 覆盖后暴露出的下一层绑定质量问题。
