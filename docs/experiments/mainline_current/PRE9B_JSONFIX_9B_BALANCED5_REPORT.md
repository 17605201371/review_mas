# Mainline-Final-v1 Clean 4B Fulltest39 Report

## 结论

这轮是干净主线 dry run：旧 sticky / progression gate / support formation pass 触发计数为 0。它可以作为后续论文结果包和 9B 确认的基线，但仍不是正式主实验。 Runtime accept/reject 仍然没有恢复真实 accept，因此二分类推荐只能作为 health check。

## Decision Health

| metric | value |
| --- | --- |
| rows | 5 |
| gold_counts | {'accept': 3, 'reject': 2, 'unknown': 0} |
| prediction_counts | {'accept': 0, 'reject': 5, 'unknown': 0} |
| accuracy | 0.4 |
| macro_f1 | 0.2857 |
| accept_recall | 0.0 |
| reject_recall | 1.0 |
| predicted_accept_count | 0 |
| false_accept_ids | 无 |
| false_reject_ids | hj323oR3rw, QAAsnSRwgu, X41c4uB4k0 |
| avg_reward | 0.3946 |

## Evidence / Support Formation

| metric | value |
| --- | --- |
| real_strong_support_total | 1 |
| nonabstract_strong_support_total | 1 |
| empirical_strong_support_total | 1 |
| method_strong_support_total | 0 |
| table_or_figure_strong_support_total | 0 |
| ablation_strong_support_total | 1 |
| abstract_strong_support_total | 0 |
| fallback_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 0 |
| accept_rows_with_2plus_real_strong_support | 0 |
| rows_with_empirical_support | 1 |
| accept_rows_with_empirical_support | 1 |

## JSON / Fallback Hygiene

| metric | value |
| --- | --- |
| evidence_json_status_counts | {'json_valid': 30} |
| evidence_json_status_turn_count | 30 |
| evidence_json_invalid_or_missing_count | 0 |
| evidence_json_fallback_used_status_count | 0 |
| evidence_json_fallback_payload_turns | 0 |

## State / Recovery

| metric | value |
| --- | --- |
| unresolved_count | 27 |
| evidence_gap_count | 15 |
| flaw_count | 5 |
| conflict_note_count | 10 |
| patch_emitted_count | 25 |
| patch_validated_count | 21 |
| patch_committed_count | 0 |
| rows_with_any_commit | 0 |
| model_generated_commit_count | 0 |
| system_salvaged_commit_count | 0 |
| recovery_failure_code_counts | {'insufficient_evidence': 6, 'no_effect_patch': 1, 'blocked_by_policy': 12, 'invalid_status_transition': 4, 'evidence_target_mismatch': 1, 'unresolved_conflict': 1} |

## Controller Cleanliness

| metric | value |
| --- | --- |
| legacy_controller_active_turns | 0 |
| policy_source_counts | {'manager_model': 6, 's4_clarification_to_evidence_override': 2, 'flaw_progress_override': 5, 'evidence_progress_override': 27} |

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
