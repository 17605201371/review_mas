# Main Experiment Readiness Audit v1

## 结论

- readiness_status: `go_for_dry_run_or_paper_pack`
- recommendation: 可以进入主试验 dry-run / 论文结果包整理；正式主试验前仍需冻结 final recommendation policy，并明确 accept/reject 只是 health check。

## 关键指标

| metric | value |
| --- | --- |
| status | go_for_dry_run_or_paper_pack |
| recommendation | 可以进入主试验 dry-run / 论文结果包整理；正式主试验前仍需冻结 final recommendation policy，并明确 accept/reject 只是 health check。 |
| blockers | none |
| warnings | strict support-quality view still has false accepts; do not use as runtime decision; runtime final decision still has zero accepts; report as health-check collapse, not primary failure |
| runtime_final_decision_counts | {"reject": 39} |
| final_recommendation_view_counts | {"borderline_positive": 12, "accept_like": 1, "not_assessable": 22, "borderline_insufficient": 3, "reject_like": 1} |
| strict_false_accept_count | 2 |
| strict_recovered_accept_ids | gzqrANCF4g |
| strict_false_accept_ids | cklg91aPGk, fGXyvmWpw6 |

## Artifact 检查

| path | exists | purpose | size_bytes |
| --- | --- | --- | --- |
| SERVER_CANONICAL_NOTE.md | yes | 服务器权威工作区说明 | 1192 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_SPEC.md | yes | 主线边界和保留/不保留模块 | 4177 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_ARTIFACT_INDEX.md | yes | 论文/外部分析文件索引 | 4523 |
| docs/experiments/mainline_current/PAPER_MAIN_RESULTS_TABLE_V1.md | yes | 论文主结果表草稿 | 2222 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md | yes | failure taxonomy | 1256 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_CASE_STUDY_PACK.md | yes | case study pack | 2322 |
| docs/experiments/mainline_current/PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md | yes | 负结果总结 | 1181 |
| outputs/results_main/review_infer/mainline_final_v1_unified_results.json | yes | 统一主线结果 JSON | 4633 |
| outputs/results_main/review_infer/final_view_invalid_binding_filter_v1_id_scoped_fulltest39.json | yes | final-view invalid binding/support-quality simulation | 45665 |
| outputs/results_main/review_infer/evidence_id_turn_scoping_v1_fulltest39_4b.jsonl | yes | ID turn-scoping fulltest39 runtime output | 14918302 |
| outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl | yes | 9B fulltest39 dry-run output | 12446841 |
| docs/experiments/mainline_current/CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39.md | yes | 9B criterion coverage/grounding audit | 7209 |
| docs/experiments/mainline_current/FINAL_RECOMMENDATION_VIEW_V1_DECISION.md | yes | final recommendation view decision | 846 |
| docs/experiments/mainline_current/MAINLINE_FINAL_V1_9B_FULLTEST39_DECISION.md | yes | 9B dry-run decision | 1654 |

## 执行边界

- 可以继续做主试验 dry-run / 论文结果包整理。
- 不建议继续新增 sticky/throttle/progression gate。
- 不建议把 support-quality 或 criterion simulation 直接接成 runtime final decision。
- 若要跑正式主试验，应先冻结 final recommendation policy，并明确二分类只是 health check。
