# Run comparison dashboard v1

- candidate: `mimo_v25_concern_recovery_contested3_mt7_smoke8_b4w4_api2_20260610_212022.jsonl` (label: contested3, papers: 8)
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
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 42 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 42 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 23 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 22 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 29 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | contested3 |
|---|---|
| `evidence_agent_worker_turns` | 42 |
| `quote_bank_nonzero_turns` | 41 |
| `payload_evidence_item_total` | 73 |
| `evidence_agent_nonempty_payload_turns` | 41 |
| `evidence_agent_question_only_turns` | 2 |
| `first_support_fallback_turns` | 4 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 38 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | contested3 |
|---|---|
| `real_strong_support_total` | 42 |
| `independent_support_group_total` | 42 |
| `diagnostic_independent_support_group_total` | 42 |
| `claims_with_2plus_independent_or_diagnostic_support` | 18 |
| `empirical_real_strong_support_count` | 23 |
| `method_real_strong_support_count` | 19 |
| `table_or_figure_real_strong_support_count` | 15 |
| `result_or_experiment_real_strong_support_count` | 8 |
| `ablation_real_strong_support_count` | 0 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 0 |
| `moderate_diagnostic_support_total` | 0 |
| `moderate_absorbed_into_final_strong_count` | 22 |
| `moderate_remaining_diagnostic_count` | 0 |
| `diagnostic_support_signal_total` | 42 |
| `papers_with_real_strong_support` | 8 |
| `papers_with_empirical_support` | 8 |
| `papers_with_deep_support` | 8 |
| `positive_coverage_gap_papers` | 0 |
| `empirical_coverage_gap_papers` | 0 |
| `deep_support_gap_papers` | 0 |
| `claims_with_real_strong_support` | 24 |
| `claims_with_empirical_real_strong_support` | 17 |
| `claims_with_deep_support` | 22 |
| `claims_with_2plus_independent_support` | 18 |
| `primary_claim_total` | 24 |
| `primary_claims_with_real_strong_support` | 20 |
| `primary_claims_with_empirical_support` | 14 |
| `primary_claims_with_deep_support` | 19 |
| `zero_real_papers` | 0 |
| `final_support_total` | 42 |
| `final_support_direct_strong_count` | 20 |
| `final_support_promoted_from_medium_count` | 22 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 0 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 0 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 43 |
| `support_trace_included_count` | 42 |
| `support_trace_dropped_count` | 1 |
| `support_trace_hygiene_filtered_count` | 0 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 0 |
| `support_trace_semantic_mismatch_count` | 1 |
| `support_trace_duplicate_quote_count` | 0 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 29 |
| `final_support_weak_locator_count` | 13 |

## Negative & flaws

| metric | contested3 |
|---|---|
| `negative_evidence_candidate_count` | 4 |
| `negative_evidence_linked_to_flaw_count` | 4 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 4 |
| `verified_actionable_negative_flaw_count` | 2 |
| `verified_limitation_negative_flaw_count` | 2 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 1 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_overclaim` | 1 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 2 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 2 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 2 |
| `negative_grounding_conflict_count` | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 |
| `negative_semantic_anchor_conflict_count` | 0 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 0 |
| `downgraded_flaw_count` | 0 |
| `potential_concern_count` | 2 |

## State contamination

| metric | contested3 |
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

| metric | contested3 |
|---|---|
| `contested_support_total` | 6 |
| `contested_final_support_total` | 6 |
| `claims_with_contested_support` | 3 |
| `claims_with_contested_final_support` | 3 |
| `open_conflict_count` | 0 |

## Gap cleanup & locator

| metric | contested3 |
|---|---|
| `evidence_gap_open_count` | 0 |
| `evidence_gap_resolved_count` | 22 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 6 |
| `state_hygiene_open_gap_count` | 0 |
| `state_hygiene_stale_gap_count` | 0 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 0 |
| `targeted_open_gap_count` | 0 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 0 |
| `unresolved_open_raw_count` | 25 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 25 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 29 |
| `programmatic_weak_locator_count` | 13 |
| `programmatic_locator_type_table_count` | 5 |
| `programmatic_locator_type_figure_count` | 12 |
| `programmatic_locator_type_section_count` | 11 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 1 |
| `programmatic_locator_type_generic_count` | 13 |
| `programmatic_high_confidence_locator_count` | 29 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | contested3 |
|---|---|
| `recovery_attempted` | 8 |
| `recovery_patch_validated` | 3 |
| `recovery_patch_committed` | 3 |
| `recovery_committed` | 3 |
| `recovery_success` | 3 |
| `hygiene_delta_improved` | 3 |
| `recovery_effective_repair` | 3 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_safe_resolution` | 7 |
| `recovery_safe_resolution_or_clean_state` | 8 |
| `hygiene_delta_or_safe_block` | 7 |
| `hygiene_delta_or_safe_block_or_clean_state` | 8 |
| `recovery_safe_blocked_weak_target` | 1 |
| `recovery_safe_blocked_terminal_target` | 3 |
| `recovery_terminal_turns` | 3 |
| `recovery_repeat_allowed_false_turns` | 3 |
| `recovery_target_gate_real_target_turns` | 2 |
| `recovery_target_gate_negative_verified_target_turns` | 3 |
| `recovery_target_gate_weak_target_turns` | 1 |
| `recovery_target_gate_fallback_target_turns` | 2 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 5 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 3 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | contested3 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | contested3 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 5 | **safe_blocked_patch (policy restriction/abstention)** |
| `SUCCESS` | 3 | **recovery_patch_committed** |

## Final decision distribution

| decision | contested3 |
|---|---|
| `accept` | 6 |
| `reject` | 2 |
