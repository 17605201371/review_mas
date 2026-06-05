# Evidence Claim Binding Guard v1 Fulltest39 Compare

## 对照对象

本文件比较三版 fulltest39：`Evidence JSON Contract v1`、`Evidence ID Turn-Scoping v1`、`Evidence Claim Binding Guard v1`。

## 核心指标

| 指标 | json_contract_v1 | id_turn_scoping_v1 | claim_binding_guard_v1 |
|---|---|---|---|
| 样本数 | 39 | 39 | 39 |
| avg_reward | 0.502463 | 0.491294 | 0.496258 |
| accuracy | 0.769231 | 0.74359 | 0.74359 |
| accept_recall | 0 | 0 | 0 |
| reject_recall | 1 | 0.966667 | 0.966667 |
| macro_f1 | 0.434783 | 0.426471 | 0.426471 |
| pred_accept_count | 0 | 1 | 1 |
| false_accept_ids | [] | ['cklg91aPGk'] | ['mHv6wcBb0z'] |
| payload_evidence_total | 161 | 146 | 143 |
| payload_unique_total | 75 | 142 | 137 |
| rows_payload_dup | 33 | 2 | 3 |
| final_evidence_total | 75 | 142 | 139 |
| final_real_strong | 13 | 14 | 13 |
| rows_final_2plus_real | 1 | 4 | 3 |
| accept_final_real_strong | 2 | 3 | 1 |
| accept_rows_final_2plus_real | 0 | 1 | 0 |
| accept_payload_real_strong | 12 | 9 | 1 |
| accept_rows_payload_2plus_real | 4 | 3 | 0 |
| invalid_bound | 4 | 23 | 0 |
| invalid_unbound | 0 | 0 | 19 |
| original_claim_id_records | 0 | 0 | 19 |
| unresolved_total | 234 | 196 | 209 |
| gaps_total | 137 | 134 | 121 |
| candidate_flaws_total | 45 | 49 | 45 |

## 关键观察

1. `Claim Binding Guard v1` 确实把 `invalid_bound` 从 `23` 降到 `0`，但这是通过在 live state merge 阶段清空 invalid evidence 的 `claim_id` 实现的。
2. 该 live mutation 明显伤到 accept-side support formation：`accept_final_real_strong 3 -> 1`，`accept_rows_final_2plus_real 1 -> 0`，`accept_payload_real_strong 9 -> 1`。
3. `final_real_strong 14 -> 13` 看起来变化不大，但 gold accept 样本上的 positive support 退化明显。
4. `invalid_unbound 0 -> 19` 和 `original_claim_id_records 19` 说明问题被从 invalid-bound 转移成 unbound，而不是转化成更可靠的 real-claim support。

## 解释

这轮结果再次验证一个原则：**state hygiene 不应放在 live trajectory 的 merge 阶段做。** Live 清理会改变后续 manager / evidence / recovery 路径，并压缩本来可能形成的正向证据。invalid binding 是真实问题，但处理位置应后移到 final-view / support-quality 过滤层。
