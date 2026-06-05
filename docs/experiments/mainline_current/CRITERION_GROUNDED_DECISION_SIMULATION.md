# Criterion-Grounded Decision Simulation v1

输入文件：`outputs/results_main/review_infer/evidence_fallback_target_isolation_v1_1_fulltest39.jsonl`

## 模拟结果

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept(strict) | borderline | false_accept | recovered_accept | pred_accept(lenient) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim0_current_rule | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 |  |  | - |
| sim1_support_count_rule | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 |  |  | - |
| sim2_criterion_gated_reject | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 3 |  |  | - |
| sim3_support_quality_accept | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 3 |  |  | - |
| sim4_combined_criterion_support_hygiene | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 3 |  |  | 3 |

## 关键读法

- `strict` 映射中，borderline / not_assessable 仍按 reject 计算，用于安全下界。
- `lenient` 只用于 Sim 4，把 borderline 视为 accept，以观察上界风险。
- 本轮不把 novelty / soundness 等维度直接接入 runtime decision。
