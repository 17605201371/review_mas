# Criterion-Grounded Decision Simulation v1

输入文件：`outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl`

## 模拟结果

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept(strict) | borderline | false_accept | recovered_accept | pred_accept(lenient) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim0_current_rule | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 |  |  | - |
| sim1_support_count_rule | 0.6923 | 0.6201 | 0.5556 | 0.7333 | 13 | 0 | ye3NrNrYOY, WNxlJJIEVj, WpXq5n8yLb, NnExMNiTHw, WLgbjzKJkk, aTBE70xiFw, kam84eEmub, aRxLDcxFcL | KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9 | - |
| sim2_criterion_gated_reject | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 16 |  |  | - |
| sim3_support_quality_accept | 0.6667 | 0.5764 | 0.4444 | 0.7333 | 12 | 4 | ye3NrNrYOY, WNxlJJIEVj, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, WLgbjzKJkk, aTBE70xiFw, kam84eEmub | KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31 | - |
| sim4_combined_criterion_support_hygiene | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 6 | ye3NrNrYOY, WpXq5n8yLb, NnExMNiTHw, a6SntIisgg, WLgbjzKJkk, aTBE70xiFw, kam84eEmub | KI9NqjLVDT, 1HCN4pjTb4, BXY6fe7q31 | 16 |

## 关键读法

- `strict` 映射中，borderline / not_assessable 仍按 reject 计算，用于安全下界。
- `lenient` 只用于 Sim 4，把 borderline 视为 accept，以观察上界风险。
- 本轮不把 novelty / soundness 等维度直接接入 runtime decision。
