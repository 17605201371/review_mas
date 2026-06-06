# Run comparison dashboard v1

- candidate: `mimo_v25_gaplink_mt7_smoke8_20260606.jsonl` (label: MIMO_GAPLINK_MT7_SMOKE8, papers: 8)
- baseline:  `mimo_v25_indgap_b4w4_mt768_smoke8_20260606.jsonl` (label: MIMO_MT768_SMOKE8, papers: 8)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 5 | smoke scaled from 20/39 | 6 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 5 | smoke scaled from 20/39 | 4 | **FAIL** |
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 30 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 30 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 17 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 15 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 20 | PASS |

**Overall protection: FAIL**

## Evidence formation health

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 32 | 45 | +13 |
| `quote_bank_nonzero_turns` | 32 | 45 | +13 |
| `payload_evidence_item_total` | 51 | 53 | +2 |
| `evidence_agent_nonempty_payload_turns` | 24 | 32 | +8 |
| `evidence_agent_question_only_turns` | 3 | 3 | 0 |
| `first_support_fallback_turns` | 2 | 3 | +1 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 30 | 30 | 0 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `real_strong_support_total` | 32 | 30 | -2 |
| `independent_support_group_total` | 32 | 30 | -2 |
| `diagnostic_independent_support_group_total` | 32 | 30 | -2 |
| `claims_with_2plus_independent_or_diagnostic_support` | 16 | 15 | -1 |
| `empirical_real_strong_support_count` | 23 | 17 | -6 |
| `method_real_strong_support_count` | 9 | 13 | +4 |
| `table_or_figure_real_strong_support_count` | 15 | 12 | -3 |
| `result_or_experiment_real_strong_support_count` | 7 | 4 | -3 |
| `ablation_real_strong_support_count` | 1 | 1 | 0 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 0 | 0 | 0 |
| `moderate_diagnostic_support_total` | 0 | 0 | 0 |
| `moderate_absorbed_into_final_strong_count` | 12 | 14 | +2 |
| `moderate_remaining_diagnostic_count` | 0 | 0 | 0 |
| `diagnostic_support_signal_total` | 32 | 30 | -2 |
| `papers_with_real_strong_support` | 8 | 8 | 0 |
| `papers_with_empirical_support` | 8 | 8 | 0 |
| `papers_with_deep_support` | 8 | 8 | 0 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 0 | 0 | 0 |
| `deep_support_gap_papers` | 0 | 0 | 0 |
| `claims_with_real_strong_support` | 16 | 15 | -1 |
| `claims_with_empirical_real_strong_support` | 14 | 11 | -3 |
| `claims_with_deep_support` | 16 | 15 | -1 |
| `claims_with_2plus_independent_support` | 16 | 15 | -1 |
| `primary_claim_total` | 24 | 24 | 0 |
| `primary_claims_with_real_strong_support` | 16 | 15 | -1 |
| `primary_claims_with_empirical_support` | 14 | 11 | -3 |
| `primary_claims_with_deep_support` | 16 | 15 | -1 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 32 | 30 | -2 |
| `final_support_direct_strong_count` | 20 | 16 | -4 |
| `final_support_promoted_from_medium_count` | 12 | 14 | +2 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 0 | 0 | 0 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 32 | 30 | -2 |
| `support_trace_included_count` | 32 | 30 | -2 |
| `support_trace_dropped_count` | 0 | 0 | 0 |
| `support_trace_hygiene_filtered_count` | 0 | 0 | 0 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 0 | 0 | 0 |
| `support_trace_semantic_mismatch_count` | 0 | 0 | 0 |
| `support_trace_duplicate_quote_count` | 0 | 0 | 0 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 20 | 20 | 0 |
| `final_support_weak_locator_count` | 12 | 10 | -2 |

## Negative & flaws

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 0 | 0 | 0 |
| `verified_actionable_negative_flaw_count` | 0 | 0 | 0 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 0 | 0 | 0 |
| `negative_type_missing_ablation` | 0 | 0 | 0 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 1 | +1 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 0 | 0 | 0 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 0 | 1 | +1 |
| `negative_grounding_conflict_count` | 0 | 1 | +1 |
| `invalid_negative_evidence_id_count_legacy` | 0 | 1 | +1 |
| `negative_semantic_anchor_conflict_count` | 0 | 1 | +1 |
| `generic_gap_semantic_rejected_count` | 0 | 1 | +1 |
| `negative_evidence_semantic_rejected_count` | 0 | 1 | +1 |
| `downgraded_flaw_count` | 0 | 0 | 0 |
| `potential_concern_count` | 0 | 0 | 0 |

## State contamination

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `state_contamination_count` | 0 | 1 | +1 |
| `state_contamination_count_legacy` | 0 | 1 | +1 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 0 | 1 | +1 |
| `state_hygiene_warning_count` | 0 | 1 | +1 |
| `weak_target_warning_count` | 0 | 1 | +1 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 0 | 1 | +1 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 0 | 0 |
| `contamination_stale_gap_persistence` | 0 | 0 | 0 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 0 | 1 | +1 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 0 | 1 | +1 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `contested_support_total` | 0 | 0 | 0 |
| `contested_final_support_total` | 0 | 0 | 0 |
| `claims_with_contested_support` | 0 | 0 | 0 |
| `claims_with_contested_final_support` | 0 | 0 | 0 |
| `open_conflict_count` | 0 | 0 | 0 |

## Gap cleanup & locator

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 0 | 0 | 0 |
| `evidence_gap_resolved_count` | 0 | 0 | 0 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 26 | 30 | +4 |
| `state_hygiene_open_gap_count` | 0 | 0 | 0 |
| `state_hygiene_stale_gap_count` | 0 | 0 | 0 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 0 | 0 | 0 |
| `targeted_open_gap_count` | 0 | 0 | 0 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 0 | 0 | 0 |
| `unresolved_open_raw_count` | 20 | 22 | +2 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 20 | 22 | +2 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 20 | 20 | 0 |
| `programmatic_weak_locator_count` | 12 | 10 | -2 |
| `programmatic_locator_type_table_count` | 5 | 4 | -1 |
| `programmatic_locator_type_figure_count` | 8 | 6 | -2 |
| `programmatic_locator_type_section_count` | 6 | 9 | +3 |
| `programmatic_locator_type_algorithm_count` | 0 | 0 | 0 |
| `programmatic_locator_type_theorem_count` | 1 | 1 | 0 |
| `programmatic_locator_type_generic_count` | 12 | 10 | -2 |
| `programmatic_high_confidence_locator_count` | 20 | 20 | 0 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `recovery_attempted` | 3 | 9 | +6 |
| `recovery_patch_validated` | 1 | 4 | +3 |
| `recovery_patch_committed` | 0 | 3 | +3 |
| `recovery_committed` | 0 | 3 | +3 |
| `recovery_success` | 0 | 3 | +3 |
| `hygiene_delta_improved` | 0 | 1 | +1 |
| `recovery_effective_repair` | 0 | 1 | +1 |
| `recovery_safe_resolution` | 2 | 6 | +4 |
| `recovery_safe_resolution_or_clean_state` | 8 | 6 | -2 |
| `hygiene_delta_or_safe_block` | 2 | 4 | +2 |
| `hygiene_delta_or_safe_block_or_clean_state` | 8 | 4 | -4 |
| `recovery_safe_blocked_weak_target` | 2 | 3 | +1 |
| `recovery_target_gate_real_target_turns` | 0 | 3 | +3 |
| `recovery_target_gate_weak_target_turns` | 3 | 5 | +2 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 0 | 1 | +1 |
| `recovery_patch_operation_reject_patch_turns` | 3 | 6 | +3 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 | 3 | +3 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Hygiene

| metric | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 2 | 4 | +2 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_TARGET_MISMATCH` | 1 | 1 | 0 | **safe_blocked_patch (missing or unverified IDs)** |
| `INVALID_STATUS_TRANSITION` | 0 | 1 | +1 | **unclassified_failure_requires_review** |
| `SUCCESS` | 0 | 3 | +3 | **recovery_patch_committed** |

## Final decision distribution

| decision | MIMO_MT768_SMOKE8 | MIMO_GAPLINK_MT7_SMOKE8 |
|---|---|---|
| `accept` | 8 | 7 |
| `reject` | 0 | 1 |
