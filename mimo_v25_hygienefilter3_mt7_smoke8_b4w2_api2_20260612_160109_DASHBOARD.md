# Run comparison dashboard v1

- candidate: `mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109.jsonl` (label: mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109, papers: 8)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 5 | smoke scaled from 20/39 | 8 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 5 | smoke scaled from 20/39 | 8 | PASS |
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 38 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 38 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 27 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 19 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 27 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `evidence_agent_worker_turns` | 37 |
| `quote_bank_nonzero_turns` | 37 |
| `payload_evidence_item_total` | 61 |
| `evidence_agent_nonempty_payload_turns` | 36 |
| `evidence_agent_question_only_turns` | 5 |
| `first_support_fallback_turns` | 12 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 27 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `real_strong_support_total` | 38 |
| `independent_support_group_total` | 38 |
| `diagnostic_independent_support_group_total` | 38 |
| `claims_with_2plus_independent_or_diagnostic_support` | 18 |
| `empirical_real_strong_support_count` | 27 |
| `method_real_strong_support_count` | 9 |
| `table_or_figure_real_strong_support_count` | 19 |
| `result_or_experiment_real_strong_support_count` | 8 |
| `ablation_real_strong_support_count` | 2 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 0 |
| `moderate_diagnostic_support_total` | 0 |
| `moderate_absorbed_into_final_strong_count` | 25 |
| `moderate_remaining_diagnostic_count` | 0 |
| `diagnostic_support_signal_total` | 38 |
| `papers_with_real_strong_support` | 8 |
| `papers_with_empirical_support` | 8 |
| `papers_with_deep_support` | 8 |
| `positive_coverage_gap_papers` | 0 |
| `empirical_coverage_gap_papers` | 0 |
| `deep_support_gap_papers` | 0 |
| `claims_with_real_strong_support` | 20 |
| `claims_with_empirical_real_strong_support` | 16 |
| `claims_with_deep_support` | 19 |
| `claims_with_2plus_independent_support` | 18 |
| `primary_claim_total` | 24 |
| `primary_claims_with_real_strong_support` | 18 |
| `primary_claims_with_empirical_support` | 14 |
| `primary_claims_with_deep_support` | 17 |
| `zero_real_papers` | 0 |
| `final_support_total` | 38 |
| `final_support_direct_strong_count` | 13 |
| `final_support_promoted_from_medium_count` | 25 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 0 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 0 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 39 |
| `support_trace_included_count` | 38 |
| `support_trace_dropped_count` | 1 |
| `support_trace_hygiene_filtered_count` | 0 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 0 |
| `support_trace_semantic_mismatch_count` | 1 |
| `support_trace_duplicate_quote_count` | 0 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 27 |
| `final_support_weak_locator_count` | 11 |

## Negative & flaws

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `negative_evidence_candidate_count` | 12 |
| `negative_evidence_linked_to_flaw_count` | 12 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 12 |
| `verified_actionable_negative_flaw_count` | 7 |
| `verified_limitation_negative_flaw_count` | 5 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 8 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_overclaim` | 2 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 14 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 7 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 6 |
| `negative_grounding_conflict_count` | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 |
| `negative_semantic_anchor_conflict_count` | 0 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 1 |
| `downgraded_flaw_count` | 1 |
| `potential_concern_count` | 7 |

## State contamination

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
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

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `contested_support_total` | 8 |
| `contested_final_support_total` | 7 |
| `claims_with_contested_support` | 4 |
| `claims_with_contested_final_support` | 4 |
| `open_conflict_count` | 0 |
| `contested_relation_final_count` | 2 |
| `contested_relation_added_count` | 2 |
| `contested_relation_effective_count` | 2 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 6 |
| `mark_contested_commit_count` | 2 |
| `mark_contested_with_positive_support_count` | 2 |
| `mark_contested_with_verified_negative_evidence_count` | 2 |
| `mark_contested_final_view_count` | 2 |
| `contested_relation_with_positive_support_count` | 2 |
| `contested_relation_with_verified_negative_evidence_count` | 2 |
| `contested_relation_final_view_count` | 2 |

## Gap cleanup & locator

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `evidence_gap_open_count` | 2 |
| `evidence_gap_resolved_count` | 20 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 10 |
| `state_hygiene_open_gap_count` | 2 |
| `state_hygiene_stale_gap_count` | 0 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 2 |
| `targeted_open_gap_count` | 2 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 0 |
| `unresolved_open_raw_count` | 23 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 23 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 27 |
| `programmatic_weak_locator_count` | 11 |
| `programmatic_locator_type_table_count` | 4 |
| `programmatic_locator_type_figure_count` | 11 |
| `programmatic_locator_type_section_count` | 11 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 1 |
| `programmatic_locator_type_generic_count` | 11 |
| `programmatic_high_confidence_locator_count` | 27 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `recovery_attempted` | 12 |
| `recovery_patch_validated` | 2 |
| `recovery_patch_committed` | 2 |
| `recovery_committed` | 2 |
| `recovery_success` | 2 |
| `hygiene_delta_improved` | 2 |
| `recovery_effective_repair` | 2 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_safe_resolution` | 6 |
| `recovery_safe_resolution_or_clean_state` | 8 |
| `hygiene_delta_or_safe_block` | 6 |
| `hygiene_delta_or_safe_block_or_clean_state` | 8 |
| `recovery_safe_blocked_weak_target` | 0 |
| `recovery_safe_blocked_terminal_target` | 4 |
| `recovery_terminal_turns` | 10 |
| `recovery_repeat_allowed_false_turns` | 10 |
| `recovery_target_gate_real_target_turns` | 6 |
| `recovery_target_gate_negative_verified_target_turns` | 6 |
| `recovery_target_gate_weak_target_turns` | 0 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 10 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 2 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 10 | **safe_blocked_patch (policy restriction/abstention)** |
| `SUCCESS` | 2 | **recovery_patch_committed** |

## Final decision distribution

| decision | mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109 |
|---|---|
| `accept` | 4 |
| `reject` | 4 |

