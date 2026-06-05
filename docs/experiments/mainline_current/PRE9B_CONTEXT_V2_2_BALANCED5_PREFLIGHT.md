# Mainline-Final-v1 Preflight Audit

## 结论

- status: `pass`
- go_for_mainline_dry_run: `True`
- go_for_formal_main_experiment: `False`
- recommendation: 可以继续 dry-run / paper pack；正式主试验前仍需使用冻结的 final recommendation policy，并把 accept/reject 作为 health check。

## Runtime Controller 开关

| flag | current_value | expected |
| --- | --- | --- |
| ENABLE_STICKY_RECOVERY_BIAS | False | must be False |
| ENABLE_PROGRESSION_GATE | False | must be False |
| ENABLE_SUPPORT_FORMATION_PASS | False | must be False |

## Runtime Controller 触发计数

输入 jsonl: `outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_balanced5_20260503.jsonl`

| signal | count |
| --- | --- |
| sticky_recovery_bias | 0 |
| progression_gate_override | 0 |
| progression_gate_triggered | 0 |
| support_formation_override | 0 |
| support_formation_pass_triggered | 0 |

## Artifact 检查

| path | exists | required | purpose | size_bytes |
| --- | --- | --- | --- | --- |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_SPEC.md | yes | required | 主线边界 spec | 5802 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_POLICY_V1_FINAL.md | yes | required | final recommendation policy 冻结口径 | 5666 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md | yes | required | 统一主线结果表 | 2101 |
| docs/experiments/mainline_current/MAIN_EXPERIMENT_READINESS_AUDIT_V1.md | yes | required | 主试验 readiness audit | 3244 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md | yes | required | artifact 索引 | 7677 |
| docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md | yes | required | 论文主结果表草稿 | 2222 |
| docs/experiments/mainline_current/SUPPORT_QUALITY_FINAL_AUDIT_9B_FULLTEST39.md | yes | optional | 9B support quality audit | 7032 |
| docs/experiments/mainline_current/CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39.md | yes | optional | 9B criterion coverage/grounding audit | 7209 |

## Blockers

- none

## Warnings

- none

## 解释

这份 preflight 只检查主线运行边界，不跑模型、不修改 runtime。它解决的是主试验前最容易污染结论的问题：旧 controller 是否误开、旧 controller 是否在 jsonl 中真实触发、关键论文结果产物是否存在。

正式主试验前必须满足：

- `ENABLE_STICKY_RECOVERY_BIAS=False`
- `ENABLE_PROGRESSION_GATE=False`
- `ENABLE_SUPPORT_FORMATION_PASS=False`
- 已选主线 jsonl 中 `sticky_recovery_bias / progression_gate_override / support_formation_override` 触发计数为 0
- `MAINLINE_FINAL_V1_SPEC.md`、`FINAL_RECOMMENDATION_POLICY_V1_FINAL.md`、主线结果表和 readiness audit 存在

若这些条件通过，可以继续做 dry-run / paper pack / 9B confirmation；但 binary accept/reject 仍只应作为 health check，不能单独作为论文主指标。
