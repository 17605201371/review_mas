# MAINLINE_FINAL_V1_9B_FULLTEST39_PAPER_PACK

## 总结论

这份结果包说明：当前系统已经从 controller 试错阶段收束到 `Mainline-Final-v1` 主线。Evidence binding、JSON robustness、empirical/non-abstract support formation 和 criterion-aware report 都已经具备论文结果层价值；runtime binary final decision 仍然是 health check，不作为论文主指标。

最关键的解释是：系统已经能形成较干净的 real-claim support，但最终推荐必须通过 final-view recommendation、support quality、hard-negative grounding 和 criterion grounding 来解释，而不能继续用二元 accept/reject 或 strong support 数量单独下结论。

## 1. Config / Controller Cleanliness

| item | value |
| --- | --- |
| preflight_status | pass |
| sticky_recovery_bias | 0 |
| progression_gate_triggered | 0 |
| support_formation_pass_triggered | 0 |
| legacy_controller_active_turns | 0 |

## 2. Runtime Decision Health Check

| metric | value |
| --- | --- |
| row_count | 39 |
| gold_accept | 9 |
| gold_reject | 30 |
| predicted_accept_count | 0 |
| predicted_reject_count | 39 |
| accuracy | 0.7692 |
| macro_f1 | 0.4348 |
| accept_recall | 0.0 |
| reject_recall | 1.0 |
| true_accept_count | 0 |
| false_accept_count | 0 |
| false_reject_count | 9 |

Runtime binary decision 仍然是 `reject=39/39`，因此不能作为主指标。它只说明原始 final decision 仍然保守，而不是 evidence / report 层没有进展。

## 3. Evidence / Support Quality

| metric | value |
| --- | --- |
| real_strong_support_total | 49 |
| nonabstract_strong_support_total | 49 |
| empirical_strong_support_total | 38 |
| method_strong_support_total | 11 |
| table_or_figure_strong_support_total | 1 |
| ablation_strong_support_total | 35 |
| abstract_strong_support_total | 0 |
| fallback_strong_support_total | 0 |
| unbound_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 17 |
| accept_rows_with_2plus_real_strong_support | 2 |
| rows_with_empirical_support | 23 |
| accept_rows_with_empirical_support | 5 |

关键点：`fallback_strong_support_total=0` 且 `strong_support_binding_precision=1.0`，说明 binding 修复站稳；`nonabstract` 与 `empirical` support 已经成为主线可报告指标。

## 4. State Burden / Recovery

| metric | value |
| --- | --- |
| unresolved_count | 269 |
| evidence_gap_count | 110 |
| flaw_count | 48 |
| conflict_note_count | 73 |
| patch_emitted_count | 96 |
| patch_validated_count | 90 |
| patch_committed_count | 1 |
| rows_with_any_commit | 1 |
| validation_to_commit_rate | 0.0111 |
| emission_to_commit_rate | 0.0104 |
| model_generated_commit_count | 1 |
| system_salvaged_commit_count | 0 |

Recovery 框架可作为结构化状态修复模块保留，但当前 commit throughput 很低，不应作为本阶段主贡献。

## 5. Final-view Recommendation

| view | count |
| --- | --- |
| accept_like | 1 |
| borderline_insufficient | 12 |
| borderline_positive | 8 |
| not_assessable_evidence_conflict | 7 |
| not_assessable_uncertain | 4 |
| reject_like | 7 |

严格 `accept_like` 只恢复 1 个 accept，且保持 0 false accept；`borderline_positive` 不能映射为 accept，否则 false accept 风险过高。正式论文应把 `borderline_positive` 写成需要人工审查的正向边界样本。

## 6. Hard-negative / Not-assessable Decomposition

| view_v4 | count |
| --- | --- |
| not_assessable_context_limited | 15 |
| not_assessable_hard_negative_unverified | 4 |
| not_assessable_targetless_unresolved | 14 |
| reject_like | 6 |

Hard-negative v2/v4 的价值在于把 `reject_like`、context-limited、targetless unresolved、hard-negative unverified 分开。当前 soft negative extraction 还不稳定，不进入 runtime，只作为离线诊断/人工审查辅助。

## 7. Criterion-aware Report

| criterion | covered | grounded | not_assessable | context_limited |
| --- | --- | --- | --- | --- |
| Novelty / Originality | 39 | 11 | 28 | 0 |
| Significance / Contribution | 39 | 28 | 11 | 0 |
| Technical Soundness | 39 | 12 | 27 | 0 |
| Empirical Adequacy | 39 | 23 | 16 | 0 |
| Clarity / Reproducibility | 39 | 28 | 11 | 0 |

Criterion section 在 final-view report v2 中稳定生成。它用于论文报告质量审计，不直接进入 runtime decision。

## 8. Soft Negative Extraction 系列结论

| run | rows | trusted_blocker_rows | parse_error_rows | conclusion |
| --- | --- | --- | --- | --- |
| 4B v1.4 diagnostic | 9 | 3 | 0 | 有潜力，但只适合作离线诊断 |
| 9B v1.4 diagnostic | 9 | 0 | 2 | 9B 未稳定复现 blocker |
| 9B compact diagnostic | 9 | 0 | 7 | compact prompt 不可靠 |

## Go / No-Go

- Go：进入论文结果整理、主试验预跑和 9B 结果包分析。
- Go：使用 final-view recommendation + support quality + criterion grounding 作为论文主指标。
- No-Go：继续做 sticky/throttle/progression gate/controller。
- No-Go：把 soft negative extraction 接入 runtime 或 final decision。
- No-Go：把 runtime binary accept/reject 准确率当主指标。
