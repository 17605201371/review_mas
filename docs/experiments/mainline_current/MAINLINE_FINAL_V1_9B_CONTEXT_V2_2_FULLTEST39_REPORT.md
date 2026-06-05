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
| avg_reward | 0.5094 |

## Evidence / Support Formation

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
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 17 |
| accept_rows_with_2plus_real_strong_support | 2 |
| rows_with_empirical_support | 23 |
| accept_rows_with_empirical_support | 5 |

## JSON / Fallback Hygiene

| metric | value |
| --- | --- |
| evidence_json_status_counts | {'json_valid': 153} |
| evidence_json_status_turn_count | 153 |
| evidence_json_invalid_or_missing_count | 0 |
| evidence_json_fallback_used_status_count | 0 |
| evidence_json_fallback_payload_turns | 0 |

## State / Recovery

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
| model_generated_commit_count | 1 |
| system_salvaged_commit_count | 0 |
| recovery_failure_code_counts | {'blocked_by_policy': 70, 'insufficient_evidence': 8, 'evidence_target_mismatch': 3, 'no_effect_patch': 8, 'invalid_status_transition': 7, 'success': 1} |

## Controller Cleanliness

| metric | value |
| --- | --- |
| legacy_controller_active_turns | 0 |
| policy_source_counts | {'manager_model': 38, 's4_clarification_to_evidence_override': 42, 'flaw_progress_override': 37, 'evidence_progress_override': 102, 'recovery_target_exhausted_override': 6, 's4_preclaim_clarification_override': 12, 'recovery_phase_override': 1, 's4_evidence_to_flaw_override': 2} |

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
