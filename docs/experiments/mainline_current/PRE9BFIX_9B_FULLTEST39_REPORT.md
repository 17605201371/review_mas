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
| avg_reward | 0.4668 |

## Evidence / Support Formation

| metric | value |
| --- | --- |
| real_strong_support_total | 1 |
| nonabstract_strong_support_total | 1 |
| empirical_strong_support_total | 0 |
| method_strong_support_total | 1 |
| table_or_figure_strong_support_total | 0 |
| ablation_strong_support_total | 0 |
| abstract_strong_support_total | 0 |
| fallback_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 0 |
| accept_rows_with_2plus_real_strong_support | 0 |
| rows_with_empirical_support | 0 |
| accept_rows_with_empirical_support | 0 |

## JSON / Fallback Hygiene

| metric | value |
| --- | --- |
| evidence_json_status_counts | {'fallback_used': 87, 'invalid_json': 25, 'json_valid': 27, 'partial_recovered': 2} |
| evidence_json_status_turn_count | 141 |
| evidence_json_invalid_or_missing_count | 25 |
| evidence_json_fallback_used_status_count | 87 |
| evidence_json_fallback_payload_turns | 87 |

## State / Recovery

| metric | value |
| --- | --- |
| unresolved_count | 212 |
| evidence_gap_count | 136 |
| flaw_count | 51 |
| conflict_note_count | 54 |
| patch_emitted_count | 40 |
| patch_validated_count | 41 |
| patch_committed_count | 4 |
| rows_with_any_commit | 3 |
| model_generated_commit_count | 1 |
| system_salvaged_commit_count | 3 |
| recovery_failure_code_counts | {'output_schema_missing': 11, 'blocked_by_policy': 34, 'success': 4, 'invalid_status_transition': 2, 'no_effect_patch': 2, 'evidence_target_mismatch': 1, 'emission_not_requested': 1} |

## Controller Cleanliness

| metric | value |
| --- | --- |
| legacy_controller_active_turns | 0 |
| policy_source_counts | {'manager_model': 85, 'evidence_progress_override': 102, 'flaw_progress_override': 21, 's4_evidence_to_flaw_override': 10, 's4_preclaim_clarification_override': 10, 's4_clarification_to_evidence_override': 6} |

## Criterion Coverage / Grounding

| criterion | covered | grounded | unsupported | meta_leakage |
| --- | --- | --- | --- | --- |
| novelty_originality | n/a | n/a | n/a | n/a |
| significance_contribution | n/a | n/a | n/a | n/a |
| technical_soundness | n/a | n/a | n/a | n/a |
| empirical_adequacy | n/a | n/a | n/a | n/a |
| clarity_reproducibility | n/a | n/a | n/a | n/a |

## 下一步

这轮先保留为 clean 4B dry-run 基线。下一步不应再加 controller；应基于这份干净 jsonl 做 final recommendation policy / support-quality / hard-negative grounding 的离线收口，确认 recommendation 口径后再做 9B 小确认。
