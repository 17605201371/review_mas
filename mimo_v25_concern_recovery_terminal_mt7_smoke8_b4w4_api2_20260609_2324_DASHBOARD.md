# Run comparison dashboard v1

- candidate: `mimo_v25_concern_recovery_terminal_mt7_smoke8_b4w4_api2_20260609_2324.jsonl` (label: TERMINAL_2324, papers: 8)
- baseline:  `mimo_v25_concern_recovery_supportrecheck_mt7_smoke8_b4w4_api2_20260609_1753.jsonl` (label: SUPPORTRECHECK_1753, papers: 8)
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
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 24 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 43 | 39 | -4 |
| `quote_bank_nonzero_turns` | 43 | 39 | -4 |
| `payload_evidence_item_total` | 75 | 60 | -15 |
| `evidence_agent_nonempty_payload_turns` | 43 | 38 | -5 |
| `evidence_agent_question_only_turns` | 3 | 4 | +1 |
| `first_support_fallback_turns` | 6 | 8 | +2 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 42 | 31 | -11 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `real_strong_support_total` | 47 | 38 | -9 |
| `independent_support_group_total` | 47 | 38 | -9 |
| `diagnostic_independent_support_group_total` | 47 | 39 | -8 |
| `claims_with_2plus_independent_or_diagnostic_support` | 21 | 19 | -2 |
| `empirical_real_strong_support_count` | 32 | 27 | -5 |
| `method_real_strong_support_count` | 15 | 11 | -4 |
| `table_or_figure_real_strong_support_count` | 15 | 19 | +4 |
| `result_or_experiment_real_strong_support_count` | 15 | 6 | -9 |
| `ablation_real_strong_support_count` | 2 | 2 | 0 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 0 | 1 | +1 |
| `moderate_diagnostic_support_total` | 0 | 1 | +1 |
| `moderate_absorbed_into_final_strong_count` | 23 | 24 | +1 |
| `moderate_remaining_diagnostic_count` | 0 | 1 | +1 |
| `diagnostic_support_signal_total` | 47 | 39 | -8 |
| `papers_with_real_strong_support` | 8 | 8 | 0 |
| `papers_with_empirical_support` | 8 | 8 | 0 |
| `papers_with_deep_support` | 8 | 8 | 0 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 0 | 0 | 0 |
| `deep_support_gap_papers` | 0 | 0 | 0 |
| `claims_with_real_strong_support` | 26 | 20 | -6 |
| `claims_with_empirical_real_strong_support` | 21 | 16 | -5 |
| `claims_with_deep_support` | 25 | 19 | -6 |
| `claims_with_2plus_independent_support` | 21 | 18 | -3 |
| `primary_claim_total` | 24 | 24 | 0 |
| `primary_claims_with_real_strong_support` | 22 | 19 | -3 |
| `primary_claims_with_empirical_support` | 17 | 15 | -2 |
| `primary_claims_with_deep_support` | 21 | 18 | -3 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 47 | 38 | -9 |
| `final_support_direct_strong_count` | 24 | 14 | -10 |
| `final_support_promoted_from_medium_count` | 23 | 24 | +1 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 0 | 0 | 0 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 48 | 39 | -9 |
| `support_trace_included_count` | 47 | 38 | -9 |
| `support_trace_dropped_count` | 1 | 1 | 0 |
| `support_trace_hygiene_filtered_count` | 0 | 1 | +1 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 0 | 0 | 0 |
| `support_trace_semantic_mismatch_count` | 1 | 0 | -1 |
| `support_trace_duplicate_quote_count` | 0 | 0 | 0 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 28 | 24 | -4 |
| `final_support_weak_locator_count` | 19 | 14 | -5 |

## Negative & flaws

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 3 | 3 | 0 |
| `negative_evidence_linked_to_flaw_count` | 3 | 3 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 3 | 3 | 0 |
| `verified_actionable_negative_flaw_count` | 2 | 2 | 0 |
| `verified_limitation_negative_flaw_count` | 1 | 1 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 2 | 2 | 0 |
| `negative_type_missing_ablation` | 0 | 0 | 0 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 1 | 1 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 2 | 2 | 0 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 2 | 3 | +1 |
| `negative_grounding_conflict_count` | 0 | 0 | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 | 0 | 0 |
| `negative_semantic_anchor_conflict_count` | 0 | 0 | 0 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 0 | 0 | 0 |
| `downgraded_flaw_count` | 0 | 0 | 0 |
| `potential_concern_count` | 2 | 2 | 0 |

## State contamination

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `state_contamination_count` | 0 | 0 | 0 |
| `state_contamination_count_legacy` | 0 | 0 | 0 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 0 | 0 | 0 |
| `state_hygiene_warning_count` | 0 | 0 | 0 |
| `weak_target_warning_count` | 0 | 0 | 0 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 0 | 0 | 0 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 0 | 0 |
| `contamination_stale_gap_persistence` | 0 | 0 | 0 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 0 | 0 | 0 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 0 | 0 | 0 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `contested_support_total` | 5 | 4 | -1 |
| `contested_final_support_total` | 5 | 4 | -1 |
| `claims_with_contested_support` | 3 | 2 | -1 |
| `claims_with_contested_final_support` | 3 | 2 | -1 |
| `open_conflict_count` | 0 | 1 | +1 |

## Gap cleanup & locator

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 0 | 2 | +2 |
| `evidence_gap_resolved_count` | 26 | 20 | -6 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 5 | 8 | +3 |
| `state_hygiene_open_gap_count` | 0 | 2 | +2 |
| `state_hygiene_stale_gap_count` | 0 | 0 | 0 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 0 | 2 | +2 |
| `targeted_open_gap_count` | 0 | 2 | +2 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 0 | 0 | 0 |
| `unresolved_open_raw_count` | 25 | 24 | -1 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 25 | 24 | -1 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 28 | 24 | -4 |
| `programmatic_weak_locator_count` | 19 | 14 | -5 |
| `programmatic_locator_type_table_count` | 6 | 2 | -4 |
| `programmatic_locator_type_figure_count` | 7 | 14 | +7 |
| `programmatic_locator_type_section_count` | 14 | 8 | -6 |
| `programmatic_locator_type_algorithm_count` | 0 | 0 | 0 |
| `programmatic_locator_type_theorem_count` | 1 | 0 | -1 |
| `programmatic_locator_type_generic_count` | 19 | 14 | -5 |
| `programmatic_high_confidence_locator_count` | 28 | 24 | -4 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `recovery_attempted` | 9 | 8 | -1 |
| `recovery_patch_validated` | 1 | 2 | +1 |
| `recovery_patch_committed` | 1 | 1 | 0 |
| `recovery_committed` | 1 | 1 | 0 |
| `recovery_success` | 1 | 1 | 0 |
| `hygiene_delta_improved` | 1 | 1 | 0 |
| `recovery_effective_repair` | 1 | 1 | 0 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 9 | 6 | -3 |
| `recovery_safe_resolution_or_clean_state` | 8 | 8 | 0 |
| `hygiene_delta_or_safe_block` | 9 | 6 | -3 |
| `hygiene_delta_or_safe_block_or_clean_state` | 8 | 8 | 0 |
| `recovery_safe_blocked_weak_target` | 8 | 3 | -5 |
| `recovery_safe_blocked_terminal_target` | 0 | 2 | +2 |
| `recovery_terminal_turns` | 0 | 2 | +2 |
| `recovery_repeat_allowed_false_turns` | 0 | 2 | +2 |
| `recovery_target_gate_real_target_turns` | 1 | 1 | 0 |
| `recovery_target_gate_negative_verified_target_turns` | 0 | 2 | +2 |
| `recovery_target_gate_weak_target_turns` | 8 | 3 | -5 |
| `recovery_target_gate_fallback_target_turns` | 0 | 2 | +2 |
| `recovery_target_gate_empty_target_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_reject_patch_turns` | 8 | 7 | -1 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 1 | 1 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Hygiene

| metric | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | SUPPORTRECHECK_1753 | TERMINAL_2324 | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 8 | 6 | -2 | **safe_blocked_patch (policy restriction/abstention)** |
| `INSUFFICIENT_EVIDENCE` | 0 | 1 | +1 | **safe_blocked_patch (insufficient evidence criteria)** |
| `SUCCESS` | 1 | 1 | 0 | **recovery_patch_committed** |

## Final decision distribution

| decision | SUPPORTRECHECK_1753 | TERMINAL_2324 |
|---|---|---|
| `accept` | 5 | 3 |
| `reject` | 3 | 5 |
