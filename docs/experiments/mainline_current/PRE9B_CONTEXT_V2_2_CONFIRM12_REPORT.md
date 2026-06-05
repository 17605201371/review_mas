# Mainline-Final-v1 Clean 4B Fulltest39 Report

## 结论

这轮是干净主线 dry run：旧 sticky / progression gate / support formation pass 触发计数为 0。它可以作为后续论文结果包和 9B 确认的基线，但仍不是正式主实验。 Runtime accept/reject 仍然没有恢复真实 accept，因此二分类推荐只能作为 health check。

## Decision Health

| metric | value |
| --- | --- |
| rows | 12 |
| gold_counts | {'accept': 6, 'reject': 6, 'unknown': 0} |
| prediction_counts | {'accept': 0, 'reject': 12, 'unknown': 0} |
| accuracy | 0.5 |
| macro_f1 | 0.3333 |
| accept_recall | 0.0 |
| reject_recall | 1.0 |
| predicted_accept_count | 0 |
| false_accept_ids | 无 |
| false_reject_ids | hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, gzqrANCF4g, KI9NqjLVDT, LebzzClHYw |
| avg_reward | 0.443 |

## Evidence / Support Formation

| metric | value |
| --- | --- |
| real_strong_support_total | 12 |
| nonabstract_strong_support_total | 12 |
| empirical_strong_support_total | 7 |
| method_strong_support_total | 5 |
| table_or_figure_strong_support_total | 0 |
| ablation_strong_support_total | 7 |
| abstract_strong_support_total | 0 |
| fallback_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 3 |
| accept_rows_with_2plus_real_strong_support | 1 |
| rows_with_empirical_support | 5 |
| accept_rows_with_empirical_support | 3 |

## JSON / Fallback Hygiene

| metric | value |
| --- | --- |
| evidence_json_status_counts | {'json_valid': 54} |
| evidence_json_status_turn_count | 54 |
| evidence_json_invalid_or_missing_count | 0 |
| evidence_json_fallback_used_status_count | 0 |
| evidence_json_fallback_payload_turns | 0 |

## State / Recovery

| metric | value |
| --- | --- |
| unresolved_count | 79 |
| evidence_gap_count | 37 |
| flaw_count | 14 |
| conflict_note_count | 24 |
| patch_emitted_count | 35 |
| patch_validated_count | 34 |
| patch_committed_count | 0 |
| rows_with_any_commit | 0 |
| model_generated_commit_count | 0 |
| system_salvaged_commit_count | 0 |
| recovery_failure_code_counts | {'blocked_by_policy': 27, 'insufficient_evidence': 3, 'evidence_target_mismatch': 3, 'no_effect_patch': 1, 'invalid_status_transition': 1} |

## Controller Cleanliness

| metric | value |
| --- | --- |
| legacy_controller_active_turns | 0 |
| policy_source_counts | {'manager_model': 13, 's4_clarification_to_evidence_override': 15, 'flaw_progress_override': 11, 'evidence_progress_override': 36, 's4_preclaim_clarification_override': 2, 's4_evidence_to_flaw_override': 1} |

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
