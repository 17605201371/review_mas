# Evidence Claim Binding Guard v1 Compare

## 对比对象

- Baseline: `evidence_id_turn_scoping_v1_mixed16.jsonl`
- Candidate: `evidence_claim_binding_guard_v1_mixed16.jsonl`

## 指标

| 指标 | ID Turn-Scoping v1 | Claim Binding Guard v1 | 变化 |
|---|---:|---:|---:|
| avg_reward | 0.438927 | 0.462282 | 0.023355 |
| payload evidence 总数 | 69 | 73 | 4 |
| payload unique evidence_id 总数 | 69 | 67 | -2 |
| payload ID 重复样本数 | 0 | 2 | 2 |
| final evidence 总数 | 69 | 67 | -2 |
| final real strong 总数 | 13 | 8 | -5 |
| final 2+ real strong 样本数 | 4 | 3 | -1 |
| invalid-bound evidence 数 | 8 | 0 | -8 |
| 标记为 invalid_claim_id 且清空 claim_id 的 evidence 数 | 0 | 12 | 12 |
| 保留 original_claim_id 的 evidence 数 | 0 | 12 | 12 |
| unresolved 总数 | 89 | 82 | -7 |
| evidence gaps 总数 | 60 | 53 | -7 |
| candidate flaws 总数 | 20 | 20 | 0 |

## 关键观察

- invalid-bound evidence 从 8 降到 0。
- 被清空 claim_id 并保留 original_claim_id 的 invalid evidence 为 12。
- avg_reward 从 0.438927 升到 0.462282。
- unresolved 从 89 降到 82，evidence gaps 从 60 降到 53。
- final real strong support 从 13 降到 8。这说明该 guard 是状态卫生修复，不是 support formation 增强；它会阻止无效绑定伪装成真实 claim evidence。
