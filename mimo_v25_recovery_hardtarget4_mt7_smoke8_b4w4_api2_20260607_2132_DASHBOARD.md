# Run comparison dashboard v1

- candidate: `mimo_v25_recovery_hardtarget4_mt7_smoke8_b4w4_api2_20260607_2132.jsonl` (label: hardtarget4_api2, papers: 8)
- baseline:  `mimo_v25_rerun_latest_mt7_smoke8_b4w4_api1_20260607_1021.jsonl` (label: rerun_api1_1021, papers: 8)
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
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 49 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 49 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 34 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 25 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 31 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 46 | 34 | -12 |
| `quote_bank_nonzero_turns` | 45 | 34 | -11 |
| `payload_evidence_item_total` | 54 | 77 | +23 |
| `evidence_agent_nonempty_payload_turns` | 30 | 34 | +4 |
| `evidence_agent_question_only_turns` | 3 | 0 | -3 |
| `first_support_fallback_turns` | 2 | 5 | +3 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 28 | 43 | +15 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `real_strong_support_total` | 30 | 49 | +19 |
| `independent_support_group_total` | 30 | 49 | +19 |
| `diagnostic_independent_support_group_total` | 30 | 50 | +20 |
| `claims_with_2plus_independent_or_diagnostic_support` | 15 | 25 | +10 |
| `empirical_real_strong_support_count` | 20 | 34 | +14 |
| `method_real_strong_support_count` | 10 | 15 | +5 |
| `table_or_figure_real_strong_support_count` | 15 | 14 | -1 |
| `result_or_experiment_real_strong_support_count` | 5 | 19 | +14 |
| `ablation_real_strong_support_count` | 0 | 1 | +1 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 0 | 1 | +1 |
| `moderate_diagnostic_support_total` | 0 | 1 | +1 |
| `moderate_absorbed_into_final_strong_count` | 17 | 36 | +19 |
| `moderate_remaining_diagnostic_count` | 0 | 1 | +1 |
| `diagnostic_support_signal_total` | 30 | 50 | +20 |
| `papers_with_real_strong_support` | 8 | 8 | 0 |
| `papers_with_empirical_support` | 8 | 8 | 0 |
| `papers_with_deep_support` | 8 | 8 | 0 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 0 | 0 | 0 |
| `deep_support_gap_papers` | 0 | 0 | 0 |
| `claims_with_real_strong_support` | 15 | 25 | +10 |
| `claims_with_empirical_real_strong_support` | 13 | 23 | +10 |
| `claims_with_deep_support` | 15 | 25 | +10 |
| `claims_with_2plus_independent_support` | 15 | 24 | +9 |
| `primary_claim_total` | 24 | 24 | 0 |
| `primary_claims_with_real_strong_support` | 15 | 20 | +5 |
| `primary_claims_with_empirical_support` | 13 | 18 | +5 |
| `primary_claims_with_deep_support` | 15 | 20 | +5 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 30 | 49 | +19 |
| `final_support_direct_strong_count` | 13 | 13 | 0 |
| `final_support_promoted_from_medium_count` | 17 | 36 | +19 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 0 | 0 | 0 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 30 | 52 | +22 |
| `support_trace_included_count` | 30 | 49 | +19 |
| `support_trace_dropped_count` | 0 | 3 | +3 |
| `support_trace_hygiene_filtered_count` | 0 | 1 | +1 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 0 | 2 | +2 |
| `support_trace_semantic_mismatch_count` | 0 | 0 | 0 |
| `support_trace_duplicate_quote_count` | 0 | 0 | 0 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 20 | 31 | +11 |
| `final_support_weak_locator_count` | 10 | 18 | +8 |

## Negative & flaws

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 1 | 0 | -1 |
| `negative_evidence_linked_to_flaw_count` | 1 | 0 | -1 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 1 | 0 | -1 |
| `verified_actionable_negative_flaw_count` | 1 | 0 | -1 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 1 | 0 | -1 |
| `negative_type_missing_ablation` | 0 | 1 | +1 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 1 | 0 | -1 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 1 | 1 | 0 |
| `negative_grounding_conflict_count` | 0 | 0 | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 | 0 | 0 |
| `negative_semantic_anchor_conflict_count` | 0 | 0 | 0 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 0 | 0 | 0 |
| `downgraded_flaw_count` | 0 | 0 | 0 |
| `potential_concern_count` | 1 | 0 | -1 |

## State contamination

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
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

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `contested_support_total` | 2 | 0 | -2 |
| `contested_final_support_total` | 2 | 0 | -2 |
| `claims_with_contested_support` | 1 | 0 | -1 |
| `claims_with_contested_final_support` | 1 | 0 | -1 |
| `open_conflict_count` | 2 | 2 | 0 |

## Gap cleanup & locator

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 2 | 0 | -2 |
| `evidence_gap_resolved_count` | 15 | 26 | +11 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 12 | 5 | -7 |
| `state_hygiene_open_gap_count` | 2 | 0 | -2 |
| `state_hygiene_stale_gap_count` | 0 | 0 | 0 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 2 | 0 | -2 |
| `targeted_open_gap_count` | 2 | 0 | -2 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 0 | 0 | 0 |
| `unresolved_open_raw_count` | 25 | 24 | -1 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 25 | 24 | -1 |
| `targetless_unresolved_deferred_count` | 5 | 5 | 0 |
| `programmatic_specific_locator_count` | 20 | 31 | +11 |
| `programmatic_weak_locator_count` | 10 | 18 | +8 |
| `programmatic_locator_type_table_count` | 3 | 2 | -1 |
| `programmatic_locator_type_figure_count` | 11 | 7 | -4 |
| `programmatic_locator_type_section_count` | 5 | 20 | +15 |
| `programmatic_locator_type_algorithm_count` | 0 | 0 | 0 |
| `programmatic_locator_type_theorem_count` | 1 | 2 | +1 |
| `programmatic_locator_type_generic_count` | 10 | 18 | +8 |
| `programmatic_high_confidence_locator_count` | 20 | 31 | +11 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `recovery_attempted` | 9 | 0 | -9 |
| `recovery_patch_validated` | 3 | 0 | -3 |
| `recovery_patch_committed` | 2 | 0 | -2 |
| `recovery_committed` | 2 | 0 | -2 |
| `recovery_success` | 2 | 0 | -2 |
| `hygiene_delta_improved` | 1 | 0 | -1 |
| `recovery_effective_repair` | 1 | 0 | -1 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 5 | 0 | -5 |
| `recovery_safe_resolution_or_clean_state` | 8 | 8 | 0 |
| `hygiene_delta_or_safe_block` | 4 | 0 | -4 |
| `hygiene_delta_or_safe_block_or_clean_state` | 8 | 8 | 0 |
| `recovery_safe_blocked_weak_target` | 3 | 0 | -3 |
| `recovery_target_gate_real_target_turns` | 2 | 0 | -2 |
| `recovery_target_gate_weak_target_turns` | 6 | 0 | -6 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 1 | 0 | -1 |
| `recovery_patch_operation_reject_patch_turns` | 7 | 0 | -7 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 2 | 0 | -2 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Hygiene

| metric | rerun_api1_1021 | hardtarget4_api2 | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | rerun_api1_1021 | hardtarget4_api2 | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 4 | 0 | -4 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_TARGET_MISMATCH` | 1 | 0 | -1 | **safe_blocked_patch (missing or unverified IDs)** |
| `INVALID_STATUS_TRANSITION` | 1 | 0 | -1 | **unclassified_failure_requires_review** |
| `SUCCESS` | 2 | 0 | -2 | **recovery_patch_committed** |
| `UNKNOWN_TARGET` | 1 | 0 | -1 | **unclassified_failure_requires_review** |

## Final decision distribution

| decision | rerun_api1_1021 | hardtarget4_api2 |
|---|---|---|
| `accept` | 5 | 6 |
| `reject` | 3 | 2 |

