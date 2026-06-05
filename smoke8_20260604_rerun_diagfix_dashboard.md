# Run comparison dashboard v1

- candidate: `smoke8_20260604_rerun_diagfix_qwen35_t7.jsonl` (label: diagfix_rerun8, papers: 8)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution` | `>=` | 5 | smoke scaled from 20/39 | 8 | PASS |
| `hygiene_delta_or_safe_block` | `>=` | 5 | smoke scaled from 20/39 | 8 | PASS |
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 10 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 8 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 9 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 7 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 6 | PASS |

**Overall protection: PASS**

## Positive support

| metric | diagfix_rerun8 |
|---|---|
| `real_strong_support_total` | 10 |
| `independent_support_group_total` | 8 |
| `diagnostic_independent_support_group_total` | 10 |
| `claims_with_2plus_independent_or_diagnostic_support` | 0 |
| `empirical_real_strong_support_count` | 9 |
| `method_real_strong_support_count` | 1 |
| `table_or_figure_real_strong_support_count` | 3 |
| `result_or_experiment_real_strong_support_count` | 4 |
| `ablation_real_strong_support_count` | 2 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 6 |
| `moderate_diagnostic_support_total` | 6 |
| `moderate_absorbed_into_final_strong_count` | 2 |
| `moderate_remaining_diagnostic_count` | 6 |
| `diagnostic_support_signal_total` | 16 |
| `papers_with_real_strong_support` | 6 |
| `papers_with_empirical_support` | 5 |
| `papers_with_deep_support` | 5 |
| `positive_coverage_gap_papers` | 2 |
| `empirical_coverage_gap_papers` | 3 |
| `deep_support_gap_papers` | 3 |
| `claims_with_real_strong_support` | 8 |
| `claims_with_empirical_real_strong_support` | 7 |
| `claims_with_deep_support` | 7 |
| `claims_with_2plus_independent_support` | 0 |
| `primary_claim_total` | 24 |
| `primary_claims_with_real_strong_support` | 8 |
| `primary_claims_with_empirical_support` | 7 |
| `primary_claims_with_deep_support` | 7 |
| `zero_real_papers` | 2 |
| `final_support_total` | 10 |
| `final_support_direct_strong_count` | 8 |
| `final_support_promoted_from_medium_count` | 2 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 1 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 1 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 18 |
| `support_trace_included_count` | 10 |
| `support_trace_dropped_count` | 8 |
| `support_trace_hygiene_filtered_count` | 2 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 1 |
| `support_trace_semantic_mismatch_count` | 1 |
| `support_trace_duplicate_quote_count` | 4 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 6 |
| `final_support_weak_locator_count` | 4 |

## Negative & flaws

| metric | diagfix_rerun8 |
|---|---|
| `negative_evidence_candidate_count` | 3 |
| `negative_evidence_linked_to_flaw_count` | 3 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 3 |
| `verified_actionable_negative_flaw_count` | 1 |
| `verified_limitation_negative_flaw_count` | 2 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 1 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_limitation` | 2 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 1 |
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

| metric | diagfix_rerun8 |
|---|---|
| `state_contamination_count` | 2 |
| `state_contamination_count_legacy` | 2 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 2 |
| `state_hygiene_warning_count` | 2 |
| `weak_target_warning_count` | 2 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 2 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 2 |
| `contamination_stale_gap_persistence` | 0 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 0 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 2 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | diagfix_rerun8 |
|---|---|
| `contested_support_total` | 1 |
| `contested_final_support_total` | 1 |
| `claims_with_contested_support` | 1 |
| `claims_with_contested_final_support` | 1 |
| `open_conflict_count` | 3 |

## Gap cleanup & locator

| metric | diagfix_rerun8 |
|---|---|
| `evidence_gap_open_count` | 25 |
| `evidence_gap_resolved_count` | 10 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 0 |
| `state_hygiene_open_gap_count` | 25 |
| `state_hygiene_stale_gap_count` | 0 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 25 |
| `targeted_open_gap_count` | 25 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 15 |
| `unresolved_open_raw_count` | 55 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 40 |
| `targetless_unresolved_deferred_count` | 37 |
| `programmatic_specific_locator_count` | 6 |
| `programmatic_weak_locator_count` | 4 |
| `programmatic_locator_type_table_count` | 2 |
| `programmatic_locator_type_figure_count` | 2 |
| `programmatic_locator_type_section_count` | 2 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 4 |
| `programmatic_high_confidence_locator_count` | 6 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | diagfix_rerun8 |
|---|---|
| `recovery_attempted` | 11 |
| `recovery_patch_validated` | 5 |
| `recovery_patch_committed` | 2 |
| `recovery_committed` | 2 |
| `recovery_success` | 2 |
| `hygiene_delta_improved` | 2 |
| `recovery_effective_repair` | 2 |
| `recovery_safe_resolution` | 8 |
| `hygiene_delta_or_safe_block` | 8 |
| `recovery_safe_blocked_weak_target` | 6 |
| `recovery_target_gate_real_target_turns` | 2 |
| `recovery_target_gate_weak_target_turns` | 6 |
| `recovery_target_gate_fallback_target_turns` | 3 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 9 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 2 |
| `recovery_patch_operation_mark_contested_turns` | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | diagfix_rerun8 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | diagfix_rerun8 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 6 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_TARGET_MISMATCH` | 1 | **safe_blocked_patch (missing or unverified IDs)** |
| `INSUFFICIENT_EVIDENCE` | 2 | **safe_blocked_patch (insufficient evidence criteria)** |
| `SUCCESS` | 2 | **recovery_patch_committed** |

## Final decision distribution

| decision | diagfix_rerun8 |
|---|---|
| `reject` | 8 |

