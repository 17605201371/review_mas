# Mainline-Final-v1 Dry-Run Reproducibility Pack

## 结论

本文件记录 `Mainline-Final-v1` 论文结果包的一键离线复现流程。本轮不跑模型、不改 runtime，只重跑现有离线汇总、case study、paper pack 和 readiness audit。当前状态可作为主试验 dry-run / 论文结果包入口，但正式主试验前仍需明确 final recommendation policy；runtime accept/reject 只作为 health check。

## Git 状态

- branch: `codex/p25-1-explicit-mainline`
- head: `84dc9ba`
- dirty_before: `M agent_system/environments/env_package/review/state.py
 M agent_system/inference/review_runner.py
 M scripts/run_mainline_final_v1_dryrun_pack.py
?? agent_system/__init__.py
?? docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_DECISION.md
?? docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_PROTOCOL.md
?? docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_SANITY.md
?? docs/experiments/mainline_current/SERVER_IMPORT_PATH_GUARD.md
?? scripts/verify_evidence_empirical_observability_v1.py`
- generated_at_utc: `2026-05-01T12:27:38.775175+00:00`

## 复现命令

| command | returncode | duration_sec |
| --- | --- | --- |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/compile_mainline_final_v1_unified_results.py | 0 | 0.048 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/compile_paper_result_pack_v1.py | 0 | 0.059 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/simulate_final_recommendation_calibration_v1.py | 0 | 0.06 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/compile_final_recommendation_calibration_case_review_v1.py | 0 | 0.051 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/audit_empirical_negative_grounding_v1.py | 0 | 0.125 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/verify_evidence_empirical_observability_v1.py | 0 | 1.732 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/compile_mainline_case_study_pack_v1.py --input-json outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json --doc-dir docs/experiments/mainline_current | 0 | 0.041 |
| /opt/conda/envs/DrMAS-qwen35/bin/python scripts/audit_main_experiment_readiness_v1.py --doc-dir docs/experiments/mainline_current | 0 | 0.041 |

## 关键指标快照

| metric | value |
| --- | --- |
| readiness_status | go_for_dry_run_or_paper_pack |
| blockers | none |
| warnings | strict support-quality view still has false accepts; do not use as runtime decision; runtime final decision still has zero accepts; report as health-check collapse, not primary failure |
| runtime_rows | 39 |
| runtime_final_decision_counts | {"reject": 39} |
| final_recommendation_view_counts | {"borderline_positive": 12, "accept_like": 1, "not_assessable": 22, "borderline_insufficient": 3, "reject_like": 1} |
| real_strong_support_total | 37 |
| non_abstract_support_total | 18 |
| empirical_support_total | 5 |
| strict_recovered_accept_ids | gzqrANCF4g |
| strict_false_accept_ids | cklg91aPGk, fGXyvmWpw6 |
| calibration_high_precision_recovered | KI9NqjLVDT, LebzzClHYw |
| calibration_high_precision_false_accept | none |
| calibration_balanced_recovered | BXY6fe7q31, KI9NqjLVDT, LebzzClHYw |
| calibration_balanced_false_accept | kam84eEmub, ye3NrNrYOY |
| empirical_negative_audit_label_counts | {"false_reject_negative_burden_or_quality_filter": 2, "other": 29, "recovered_accept_with_empirical_or_grounded_empirical": 2, "false_reject_no_real_support": 4, "false_accept_risk_positive_not_sufficient": 1, "false_accept_risk_missing_empirical_grounding": 1} |
| empirical_negative_audit_next_cut | Empirical Evidence Targeted Audit/Pass v1 |

## 产物检查

| path | exists | size_bytes | purpose |
| --- | --- | --- | --- |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md | yes | 2101 | 统一主线结果表 |
| docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md | yes | 2222 | 论文主结果表草稿 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_POLICY_V1_FINAL.md | yes | 5666 | final recommendation policy 冻结口径 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_V1_RESULTS.md | yes | 2043 | final recommendation calibration 结果 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_V1_DECISION.md | yes | 1795 | final recommendation calibration 决策 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_CALIBRATION_CASE_REVIEW_V1.md | yes | 4984 | final recommendation calibration 关键 case review |
| docs/experiments/mainline_current/EMPIRICAL_EVIDENCE_SUFFICIENCY_AUDIT_V1.md | yes | 1768 | empirical evidence sufficiency audit |
| docs/experiments/mainline_current/HARD_NEGATIVE_GROUNDING_AUDIT_V1.md | yes | 1152 | hard-negative grounding audit |
| docs/experiments/mainline_current/EMPIRICAL_NEGATIVE_CASE_TABLE_V1.md | yes | 1440 | empirical/negative grounding case table |
| docs/experiments/mainline_current/NEXT_CUT_AFTER_CALIBRATION_DECISION.md | yes | 1226 | calibration 后下一刀方向 |
| docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_PROTOCOL.md | yes | 1458 | Evidence empirical observability protocol |
| docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_SANITY.md | yes | 799 | Evidence empirical observability sanity |
| docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_DECISION.md | yes | 760 | Evidence empirical observability decision |
| docs/experiments/mainline_current/SERVER_IMPORT_PATH_GUARD.md | yes | 721 | server import path guard |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md | yes | 4523 | 主线 artifact 索引 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_CASEBOOK_V1.md | yes | 2712 | final recommendation casebook |
| docs/experiments/mainline_current/PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md | yes | 1181 | 负结果总结 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md | yes | 1256 | failure taxonomy |
| docs/experiments/mainline_current/MAIN_EXPERIMENT_READINESS_AUDIT_V1.md | yes | 3244 | 主试验 readiness audit |
| outputs/results_main/review_infer/mainline_final_v1_unified_results.json | yes | 4633 | 统一结果 JSON |
| outputs/results_main/review_infer/main_experiment_readiness_audit_v1.json | yes | 4835 | readiness audit JSON |
| outputs/results_main/review_infer/mainline_final_v1_dry_run_pack_summary.json | yes | 8609 | dry-run pack summary JSON |
| outputs/results_main/review_infer/final_recommendation_calibration_v1.json | yes | 61861 | final recommendation calibration JSON |
| outputs/results_main/review_infer/final_recommendation_calibration_case_review_v1.json | yes | 4984 | final recommendation calibration case review JSON |
| outputs/results_main/review_infer/empirical_negative_grounding_audit_v1.json | yes | 53130 | empirical/negative grounding audit JSON |
| outputs/results_main/review_infer/evidence_empirical_observability_v1_sanity.json | yes | 832 | Evidence empirical observability sanity JSON |

## 使用边界

- 这是离线结果包，不是新的模型推理实验。
- 不把 support-quality / criterion simulation 直接接成 runtime final decision。
- 不继续 sticky / throttle / progression gate。
- 论文中应将 binary accept/reject 作为 health check，将 final recommendation view、support quality、criterion grounding 和 failure taxonomy 作为主解释层。
