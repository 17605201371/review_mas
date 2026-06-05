# Mainline-Final-v1 Clean 4B Fulltest39 Report

## 结论

这轮是干净主线 dry run：旧 sticky / progression gate / support formation pass 触发计数为 0。它可以作为后续论文结果包和 9B 确认的基线，但仍不是正式主实验。 Runtime accept/reject 仍然没有恢复真实 accept，因此二分类推荐只能作为 health check。

## Decision Health

| metric | value |
| --- | --- |
| rows | 39 |
| gold_counts | {'accept': 9, 'reject': 30, 'unknown': 0} |
| prediction_counts | {'accept': 0, 'reject': 39, 'unknown': 0} |
| accuracy | 0.7692 |
| macro_f1 | 0.4348 |
| accept_recall | 0.0 |
| reject_recall | 1.0 |
| predicted_accept_count | 0 |
| false_accept_ids | 无 |
| false_reject_ids | hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, gzqrANCF4g, KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9 |
| avg_reward | 0.5043 |

## Evidence / Support Formation

| metric | value |
| --- | --- |
| real_strong_support_total | 28 |
| nonabstract_strong_support_total | 25 |
| empirical_strong_support_total | 20 |
| method_strong_support_total | 5 |
| table_or_figure_strong_support_total | 0 |
| ablation_strong_support_total | 19 |
| abstract_strong_support_total | 3 |
| fallback_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 7 |
| accept_rows_with_2plus_real_strong_support | 2 |
| rows_with_empirical_support | 16 |
| accept_rows_with_empirical_support | 4 |

## JSON / Fallback Hygiene

| metric | value |
| --- | --- |
| evidence_json_status_counts | {'json_valid': 139, 'no_json_object': 14, 'invalid_json': 12, 'fallback_used': 2, 'truncated_tagged_json': 1} |
| evidence_json_status_turn_count | 168 |
| evidence_json_invalid_or_missing_count | 27 |
| evidence_json_fallback_used_status_count | 2 |
| evidence_json_fallback_payload_turns | 2 |

## State / Recovery

| metric | value |
| --- | --- |
| unresolved_count | 190 |
| evidence_gap_count | 147 |
| flaw_count | 51 |
| conflict_note_count | 79 |
| patch_emitted_count | 109 |
| patch_validated_count | 101 |
| patch_committed_count | 6 |
| rows_with_any_commit | 6 |
| model_generated_commit_count | 3 |
| system_salvaged_commit_count | 3 |
| recovery_failure_code_counts | {'insufficient_evidence': 66, 'invalid_status_transition': 7, 'unresolved_conflict': 6, 'blocked_by_policy': 19, 'semantic_mismatch': 2, 'no_effect_patch': 3, 'success': 6, 'emission_not_requested': 1, 'evidence_target_mismatch': 1, 'output_schema_missing': 1} |

## Controller Cleanliness

| metric | value |
| --- | --- |
| legacy_controller_active_turns | 0 |
| policy_source_counts | {'manager_model': 37, 'evidence_progress_override': 137, 'flaw_progress_override': 38, 's4_evidence_to_flaw_override': 1, 's4_preclaim_clarification_override': 9, 's4_clarification_to_evidence_override': 26, 'recovery_phase_override': 2} |

## Criterion Coverage / Grounding

| criterion | covered | grounded | unsupported | meta_leakage |
| --- | --- | --- | --- | --- |
| novelty_originality | 39 | 38 | 0 | 0 |
| significance_contribution | 39 | 37 | 0 | 0 |
| technical_soundness | 39 | 27 | 0 | 0 |
| empirical_adequacy | 39 | 23 | 0 | 0 |
| clarity_reproducibility | 39 | 38 | 0 | 0 |

## 下一步

这轮先保留为 clean 4B dry-run 基线。下一步不应再加 controller；应基于这份干净 jsonl 做 final recommendation policy / support-quality / hard-negative grounding 的离线收口，确认 recommendation 口径后再做 9B 小确认。
