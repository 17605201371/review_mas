# Evidence JSON Contract v1 对比结果

## 对比口径

本轮使用固定 mixed16 输入：

- 数据集：`outputs/results_main/review_infer/support_quality_v1_mixed16.parquet`
- 模型：`Qwen3.5-4B`
- 模式：`s4`
- `max_turns=8`
- `max_workers_per_turn=2`
- `manager_batch_size=4`
- `max_model_len=3072`
- `max_tokens=640`

对比文件：

- `outputs/results_main/review_infer/evidence_context_v2_1_mixed16_3072_768.jsonl`
- `outputs/results_main/review_infer/evidence_json_robustness_v1_1_mixed16.jsonl`
- `outputs/results_main/review_infer/evidence_json_contract_v1_mixed16.jsonl`

## 汇总指标

| 指标 | Context v2.1 | JSON Robustness v1.1 | JSON Contract v1 |
| --- | ---: | ---: | ---: |
| rows | 16 | 16 | 16 |
| avg_reward | 0.3846 | 0.3968 | 0.4601 |
| Evidence worker calls | 72 | 65 | 77 |
| Evidence parse errors | 18 | 16 | 17 |
| Evidence fallback payloads | 18 | 8 | 0 |
| Partial JSON recovery | 0 | 3 | 1 |
| Turn-log JSON status rows | 0 | 0 | 77 |
| JSON valid turns | 0 | 0 | 59 |
| Invalid JSON turns | 0 | 0 | 8 |
| No JSON object turns | 0 | 0 | 7 |
| Truncated JSON object turns | 0 | 0 | 1 |
| Truncated tagged JSON turns | 0 | 0 | 1 |
| Real strong support | 5 | 5 | 9 |
| Non-abstract strong support | 1 | 2 | 4 |
| Empirical strong support | 5 | 4 | 8 |
| Fallback strong support | 0 | 0 | 0 |
| Invalid-bound evidence | 0 | 0 | 4 |
| Unresolved total | 117 | 101 | 87 |
| Evidence gaps total | 68 | 78 | 69 |
| Candidate flaws total | 25 | 29 | 25 |
| Predicted accept | 0 | 0 | 0 |

## 主要观察

1. `Evidence JSON Contract v1` 没有消灭所有 parse error，但改变了失败路径：解析失败不再大量转成 fallback payload，`Evidence fallback payloads` 从 `8` 降到 `0`。
2. 正向证据形成没有受损，反而增强：`real strong support` 从 `5` 升到 `9`，`non-abstract strong support` 从 `2` 升到 `4`，`empirical strong support` 从 `4` 升到 `8`。
3. 状态污染压力下降：`unresolved_total` 从 `101` 降到 `87`，`candidate_flaws_total` 从 `29` 降到 `25`。
4. 新增 turn-log 字段已正常落盘，77 个 Evidence turn 都有 `evidence_json_parse_status`，后续 fulltest 可以直接按 failure type 做诊断。
5. 仍有 4 条 `invalid_bound_evidence`，主要来自“当前 state 只有 fallback claim 或 claim id 不匹配”的样本。它们没有进入 fallback strong support，但说明后续仍需要 real-claim availability / binding 侧的审计。

## 论文相关解释

这轮结果支持当前论文主线：问题不是模型完全看不到证据，而是结构化证据输出契约和 fallback 路径会污染 ReviewState。通过将 Evidence Agent 输出改为 JSON-only contract，并记录失败类型，系统减少了 fallback 污染，同时提升了 real/non-abstract/empirical support。

本轮不解决 final decision collapse。16 条样本仍然全部 `reject`，说明最终推荐层仍需要 derived hygiene view、support quality、criterion-grounded aggregation 来解释，而不是继续靠 strong support 数量直接改阈值。
