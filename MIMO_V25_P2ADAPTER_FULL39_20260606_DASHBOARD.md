# Run comparison dashboard v1

- candidate: `mimo_v25_p2adapter_fulltest39_20260606.jsonl` (label: MIMO_V25_P2ADAPTER_FULL39, papers: 39)
- dashboard_mode: `full39`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 20 |  | 13 | **FAIL** |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 20 |  | 12 | **FAIL** |
| `real_strong_support_total` | `>=` | 30 |  | 145 | PASS |
| `independent_support_group_total` | `>=` | 24 |  | 145 | PASS |
| `empirical_real_strong_support_count` | `>=` | 20 |  | 99 | PASS |
| `claims_with_deep_support` | `>=` | 8 |  | 73 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 18 |  | 70 | PASS |

**Overall protection: FAIL**

## Evidence formation health

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `evidence_agent_worker_turns` | 145 |
| `quote_bank_nonzero_turns` | 145 |
| `payload_evidence_item_total` | 218 |
| `evidence_agent_nonempty_payload_turns` | 108 |
| `evidence_agent_question_only_turns` | 8 |
| `first_support_fallback_turns` | 21 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 124 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `real_strong_support_total` | 145 |
| `independent_support_group_total` | 145 |
| `diagnostic_independent_support_group_total` | 145 |
| `claims_with_2plus_independent_or_diagnostic_support` | 70 |
| `empirical_real_strong_support_count` | 99 |
| `method_real_strong_support_count` | 46 |
| `table_or_figure_real_strong_support_count` | 65 |
| `result_or_experiment_real_strong_support_count` | 30 |
| `ablation_real_strong_support_count` | 4 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 0 |
| `moderate_diagnostic_support_total` | 0 |
| `moderate_absorbed_into_final_strong_count` | 77 |
| `moderate_remaining_diagnostic_count` | 0 |
| `diagnostic_support_signal_total` | 145 |
| `papers_with_real_strong_support` | 39 |
| `papers_with_empirical_support` | 36 |
| `papers_with_deep_support` | 39 |
| `positive_coverage_gap_papers` | 0 |
| `empirical_coverage_gap_papers` | 3 |
| `deep_support_gap_papers` | 0 |
| `claims_with_real_strong_support` | 73 |
| `claims_with_empirical_real_strong_support` | 62 |
| `claims_with_deep_support` | 73 |
| `claims_with_2plus_independent_support` | 70 |
| `primary_claim_total` | 117 |
| `primary_claims_with_real_strong_support` | 73 |
| `primary_claims_with_empirical_support` | 62 |
| `primary_claims_with_deep_support` | 73 |
| `zero_real_papers` | 0 |
| `final_support_total` | 145 |
| `final_support_direct_strong_count` | 68 |
| `final_support_promoted_from_medium_count` | 77 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 0 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 0 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 145 |
| `support_trace_included_count` | 145 |
| `support_trace_dropped_count` | 0 |
| `support_trace_hygiene_filtered_count` | 0 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 0 |
| `support_trace_semantic_mismatch_count` | 0 |
| `support_trace_duplicate_quote_count` | 0 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 70 |
| `final_support_weak_locator_count` | 75 |

## Negative & flaws

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `negative_evidence_candidate_count` | 4 |
| `negative_evidence_linked_to_flaw_count` | 4 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 4 |
| `verified_actionable_negative_flaw_count` | 2 |
| `verified_limitation_negative_flaw_count` | 2 |
| `negative_type_direct_contradiction` | 1 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 1 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_limitation` | 2 |
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
| `potential_concern_count` | 0 |

## State contamination

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `state_contamination_count` | 4 |
| `state_contamination_count_legacy` | 4 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 1 |
| `conservative_state_warning_count` | 3 |
| `state_hygiene_warning_count` | 3 |
| `weak_target_warning_count` | 3 |
| `repairable_contamination_target_count` | 1 |
| `conservative_contamination_target_count` | 3 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 1 |
| `contamination_zero_real_support` | 0 |
| `contamination_stale_gap_persistence` | 1 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 1 |
| `contamination_evidence_misbinding` | 0 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 1 |
| `target_gate_real_target` | 1 |
| `target_gate_weak_target` | 3 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `contested_support_total` | 4 |
| `contested_final_support_total` | 4 |
| `claims_with_contested_support` | 2 |
| `claims_with_contested_final_support` | 2 |
| `open_conflict_count` | 0 |

## Gap cleanup & locator

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `evidence_gap_open_count` | 8 |
| `evidence_gap_resolved_count` | 3 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 132 |
| `state_hygiene_open_gap_count` | 7 |
| `state_hygiene_stale_gap_count` | 1 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 8 |
| `targeted_open_gap_count` | 8 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 0 |
| `unresolved_open_raw_count` | 107 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 107 |
| `targetless_unresolved_deferred_count` | 8 |
| `programmatic_specific_locator_count` | 70 |
| `programmatic_weak_locator_count` | 75 |
| `programmatic_locator_type_table_count` | 18 |
| `programmatic_locator_type_figure_count` | 15 |
| `programmatic_locator_type_section_count` | 35 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 2 |
| `programmatic_locator_type_generic_count` | 75 |
| `programmatic_high_confidence_locator_count` | 70 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `recovery_attempted` | 23 |
| `recovery_patch_validated` | 10 |
| `recovery_patch_committed` | 3 |
| `recovery_committed` | 3 |
| `recovery_success` | 3 |
| `hygiene_delta_improved` | 2 |
| `recovery_effective_repair` | 2 |
| `recovery_safe_resolution` | 13 |
| `recovery_safe_resolution_or_clean_state` | 13 |
| `hygiene_delta_or_safe_block` | 12 |
| `hygiene_delta_or_safe_block_or_clean_state` | 12 |
| `recovery_safe_blocked_weak_target` | 10 |
| `recovery_target_gate_real_target_turns` | 3 |
| `recovery_target_gate_weak_target_turns` | 16 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 4 |
| `recovery_patch_operation_reject_patch_turns` | 20 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 2 |
| `recovery_patch_operation_mark_contested_turns` | 1 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | MIMO_V25_P2ADAPTER_FULL39 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 12 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_TARGET_MISMATCH` | 3 | **safe_blocked_patch (missing or unverified IDs)** |
| `INSUFFICIENT_EVIDENCE` | 2 | **safe_blocked_patch (insufficient evidence criteria)** |
| `INVALID_STATUS_TRANSITION` | 1 | **unclassified_failure_requires_review** |
| `NO_EFFECT_PATCH` | 1 | **unclassified_failure_requires_review** |
| `SUCCESS` | 3 | **recovery_patch_committed** |
| `UNRESOLVED_CONFLICT` | 1 | **unclassified_failure_requires_review** |

## Final decision distribution

| decision | MIMO_V25_P2ADAPTER_FULL39 |
|---|---|
| `accept` | 31 |
| `reject` | 8 |

