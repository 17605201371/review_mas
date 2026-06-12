# Run comparison dashboard v1

- candidate: `mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757.jsonl` (label: mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757, papers: 20)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 99 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 99 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 78 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 52 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 63 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `evidence_agent_worker_turns` | 95 |
| `quote_bank_nonzero_turns` | 95 |
| `payload_evidence_item_total` | 128 |
| `evidence_agent_nonempty_payload_turns` | 95 |
| `evidence_agent_question_only_turns` | 23 |
| `first_support_fallback_turns` | 38 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 63 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `real_strong_support_total` | 99 |
| `independent_support_group_total` | 99 |
| `diagnostic_independent_support_group_total` | 100 |
| `claims_with_2plus_independent_or_diagnostic_support` | 47 |
| `empirical_real_strong_support_count` | 78 |
| `method_real_strong_support_count` | 21 |
| `table_or_figure_real_strong_support_count` | 53 |
| `result_or_experiment_real_strong_support_count` | 19 |
| `ablation_real_strong_support_count` | 6 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 1 |
| `moderate_diagnostic_support_total` | 1 |
| `moderate_absorbed_into_final_strong_count` | 70 |
| `moderate_remaining_diagnostic_count` | 1 |
| `diagnostic_support_signal_total` | 100 |
| `papers_with_real_strong_support` | 20 |
| `papers_with_empirical_support` | 20 |
| `papers_with_deep_support` | 20 |
| `positive_coverage_gap_papers` | 0 |
| `empirical_coverage_gap_papers` | 0 |
| `deep_support_gap_papers` | 0 |
| `claims_with_real_strong_support` | 52 |
| `claims_with_empirical_real_strong_support` | 50 |
| `claims_with_deep_support` | 52 |
| `claims_with_2plus_independent_support` | 47 |
| `primary_claim_total` | 60 |
| `primary_claims_with_real_strong_support` | 45 |
| `primary_claims_with_empirical_support` | 43 |
| `primary_claims_with_deep_support` | 45 |
| `zero_real_papers` | 0 |
| `final_support_total` | 99 |
| `final_support_direct_strong_count` | 29 |
| `final_support_promoted_from_medium_count` | 70 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 0 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 0 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 100 |
| `support_trace_included_count` | 99 |
| `support_trace_dropped_count` | 1 |
| `support_trace_hygiene_filtered_count` | 1 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 0 |
| `support_trace_semantic_mismatch_count` | 0 |
| `support_trace_duplicate_quote_count` | 0 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 63 |
| `final_support_weak_locator_count` | 36 |

## Negative & flaws

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `negative_evidence_candidate_count` | 12 |
| `negative_evidence_linked_to_flaw_count` | 12 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 13 |
| `verified_actionable_negative_flaw_count` | 6 |
| `verified_limitation_negative_flaw_count` | 7 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 3 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 6 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_overclaim` | 0 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 14 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 6 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 9 |
| `negative_grounding_conflict_count` | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 |
| `negative_semantic_anchor_conflict_count` | 0 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 2 |
| `downgraded_flaw_count` | 1 |
| `potential_concern_count` | 6 |

## State contamination

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `state_contamination_count` | 0 |
| `state_contamination_count_legacy` | 0 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 0 |
| `state_hygiene_warning_count` | 0 |
| `weak_target_warning_count` | 0 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 0 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 0 |
| `contamination_stale_gap_persistence` | 0 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 0 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 0 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `contested_support_total` | 12 |
| `contested_final_support_total` | 12 |
| `claims_with_contested_support` | 6 |
| `claims_with_contested_final_support` | 6 |
| `open_conflict_count` | 0 |
| `contested_relation_final_count` | 7 |
| `contested_relation_added_count` | 7 |
| `contested_relation_effective_count` | 7 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 8 |
| `mark_contested_commit_count` | 7 |
| `mark_contested_with_positive_support_count` | 7 |
| `mark_contested_with_verified_negative_evidence_count` | 7 |
| `mark_contested_final_view_count` | 7 |
| `contested_relation_with_positive_support_count` | 7 |
| `contested_relation_with_verified_negative_evidence_count` | 7 |
| `contested_relation_final_view_count` | 7 |

## Gap cleanup & locator

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `evidence_gap_open_count` | 1 |
| `evidence_gap_resolved_count` | 52 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 21 |
| `state_hygiene_open_gap_count` | 1 |
| `state_hygiene_stale_gap_count` | 0 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 1 |
| `targeted_open_gap_count` | 1 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 0 |
| `unresolved_open_raw_count` | 52 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 52 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 63 |
| `programmatic_weak_locator_count` | 36 |
| `programmatic_locator_type_table_count` | 22 |
| `programmatic_locator_type_figure_count` | 13 |
| `programmatic_locator_type_section_count` | 27 |
| `programmatic_locator_type_algorithm_count` | 1 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 36 |
| `programmatic_high_confidence_locator_count` | 63 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `recovery_attempted` | 14 |
| `recovery_patch_validated` | 7 |
| `recovery_patch_committed` | 7 |
| `recovery_committed` | 7 |
| `recovery_success` | 7 |
| `hygiene_delta_improved` | 7 |
| `recovery_effective_repair` | 7 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_safe_resolution` | 8 |
| `recovery_safe_resolution_or_clean_state` | 20 |
| `hygiene_delta_or_safe_block` | 8 |
| `hygiene_delta_or_safe_block_or_clean_state` | 20 |
| `recovery_safe_blocked_weak_target` | 0 |
| `recovery_safe_blocked_terminal_target` | 1 |
| `recovery_terminal_turns` | 6 |
| `recovery_repeat_allowed_false_turns` | 6 |
| `recovery_target_gate_real_target_turns` | 5 |
| `recovery_target_gate_negative_verified_target_turns` | 8 |
| `recovery_target_gate_weak_target_turns` | 0 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 1 |
| `recovery_patch_operation_reject_patch_turns` | 7 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 7 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 7 | **safe_blocked_patch (policy restriction/abstention)** |
| `SUCCESS` | 7 | **recovery_patch_committed** |

## Final decision distribution

| decision | mimo_v25_hygienefilter3_hardneg20_mt7_b4w2_api2_20260612_162757 |
|---|---|
| `accept` | 14 |
| `reject` | 6 |

