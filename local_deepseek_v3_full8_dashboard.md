# Run comparison dashboard v1

- candidate: `local_deepseek_v3_full8.jsonl` (label: deepseek_full8, papers: 8)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution` | `>=` | 5 | smoke scaled from 20/39 | 5 | PASS |
| `hygiene_delta_or_safe_block` | `>=` | 5 | smoke scaled from 20/39 | 2 | **FAIL** |
| `real_strong_support_total` | `>=` | 7 | smoke scaled from 30/39 | 23 | PASS |
| `independent_support_group_total` | `>=` | 5 | smoke scaled from 24/39 | 19 | PASS |
| `empirical_real_strong_support_count` | `>=` | 5 | smoke scaled from 20/39 | 19 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 11 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 4 | smoke scaled from 18/39 | 14 | PASS |

**Overall protection: FAIL**

## Evidence formation health

| metric | deepseek_full8 |
|---|---|
| `evidence_agent_worker_turns` | 44 |
| `quote_bank_nonzero_turns` | 42 |
| `payload_evidence_item_total` | 57 |
| `evidence_agent_nonempty_payload_turns` | 34 |
| `evidence_agent_question_only_turns` | 2 |
| `first_support_fallback_turns` | 0 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | deepseek_full8 |
|---|---|
| `real_strong_support_total` | 23 |
| `independent_support_group_total` | 19 |
| `diagnostic_independent_support_group_total` | 0 |
| `claims_with_2plus_independent_or_diagnostic_support` | 0 |
| `empirical_real_strong_support_count` | 19 |
| `method_real_strong_support_count` | 4 |
| `table_or_figure_real_strong_support_count` | 10 |
| `result_or_experiment_real_strong_support_count` | 7 |
| `ablation_real_strong_support_count` | 2 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 24 |
| `moderate_diagnostic_support_total` | 24 |
| `moderate_absorbed_into_final_strong_count` | 7 |
| `moderate_remaining_diagnostic_count` | 24 |
| `diagnostic_support_signal_total` | 47 |
| `papers_with_real_strong_support` | 7 |
| `papers_with_empirical_support` | 7 |
| `papers_with_deep_support` | 7 |
| `positive_coverage_gap_papers` | 1 |
| `empirical_coverage_gap_papers` | 1 |
| `deep_support_gap_papers` | 1 |
| `claims_with_real_strong_support` | 12 |
| `claims_with_empirical_real_strong_support` | 11 |
| `claims_with_deep_support` | 11 |
| `claims_with_2plus_independent_support` | 5 |
| `primary_claim_total` | 24 |
| `primary_claims_with_real_strong_support` | 12 |
| `primary_claims_with_empirical_support` | 11 |
| `primary_claims_with_deep_support` | 11 |
| `zero_real_papers` | 1 |
| `final_support_total` | 23 |
| `final_support_direct_strong_count` | 16 |
| `final_support_promoted_from_medium_count` | 7 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 2 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 2 |
| `near_miss_promoted_to_final_count` | 1 |
| `support_trace_total` | 68 |
| `support_trace_included_count` | 23 |
| `support_trace_dropped_count` | 45 |
| `support_trace_hygiene_filtered_count` | 22 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 12 |
| `support_trace_semantic_mismatch_count` | 9 |
| `support_trace_duplicate_quote_count` | 2 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 14 |
| `final_support_weak_locator_count` | 9 |

## Negative & flaws

| metric | deepseek_full8 |
|---|---|
| `negative_evidence_candidate_count` | 2 |
| `negative_evidence_linked_to_flaw_count` | 2 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 4 |
| `verified_actionable_negative_flaw_count` | 0 |
| `verified_limitation_negative_flaw_count` | 4 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 0 |
| `negative_type_missing_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_limitation` | 4 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 0 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 5 |
| `negative_grounding_conflict_count` | 4 |
| `invalid_negative_evidence_id_count_legacy` | 4 |
| `negative_semantic_anchor_conflict_count` | 4 |
| `generic_gap_semantic_rejected_count` | 4 |
| `negative_evidence_semantic_rejected_count` | 4 |
| `downgraded_flaw_count` | 0 |
| `potential_concern_count` | 1 |

## State contamination

| metric | deepseek_full8 |
|---|---|
| `state_contamination_count` | 7 |
| `state_contamination_count_legacy` | 7 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 1 |
| `conservative_state_warning_count` | 6 |
| `state_hygiene_warning_count` | 6 |
| `weak_target_warning_count` | 6 |
| `repairable_contamination_target_count` | 1 |
| `conservative_contamination_target_count` | 6 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 1 |
| `contamination_zero_real_support` | 1 |
| `contamination_stale_gap_persistence` | 0 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 1 |
| `contamination_evidence_misbinding` | 4 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 1 |
| `target_gate_weak_target` | 6 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | deepseek_full8 |
|---|---|
| `contested_support_total` | 3 |
| `contested_final_support_total` | 2 |
| `claims_with_contested_support` | 1 |
| `claims_with_contested_final_support` | 1 |
| `open_conflict_count` | 8 |

## Gap cleanup & locator

| metric | deepseek_full8 |
|---|---|
| `evidence_gap_open_count` | 2 |
| `evidence_gap_resolved_count` | 28 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 0 |
| `state_hygiene_open_gap_count` | 2 |
| `state_hygiene_stale_gap_count` | 0 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 2 |
| `targeted_open_gap_count` | 2 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 0 |
| `unresolved_open_raw_count` | 33 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 33 |
| `targetless_unresolved_deferred_count` | 31 |
| `programmatic_specific_locator_count` | 14 |
| `programmatic_weak_locator_count` | 9 |
| `programmatic_locator_type_table_count` | 9 |
| `programmatic_locator_type_figure_count` | 1 |
| `programmatic_locator_type_section_count` | 4 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 9 |
| `programmatic_high_confidence_locator_count` | 14 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | deepseek_full8 |
|---|---|
| `recovery_attempted` | 12 |
| `recovery_patch_validated` | 6 |
| `recovery_patch_committed` | 4 |
| `recovery_committed` | 4 |
| `recovery_success` | 4 |
| `hygiene_delta_improved` | 1 |
| `recovery_effective_repair` | 1 |
| `recovery_safe_resolution` | 5 |
| `hygiene_delta_or_safe_block` | 2 |
| `recovery_safe_blocked_weak_target` | 1 |
| `recovery_target_gate_real_target_turns` | 4 |
| `recovery_target_gate_weak_target_turns` | 2 |
| `recovery_target_gate_fallback_target_turns` | 1 |
| `recovery_target_gate_empty_target_turns` | 5 |
| `recovery_patch_operation_reject_patch_turns` | 8 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 3 |
| `recovery_patch_operation_mark_contested_turns` | 1 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Hygiene

| metric | deepseek_full8 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | deepseek_full8 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 5 | **safe_blocked_patch (policy restriction/abstention)** |
| `INSUFFICIENT_EVIDENCE` | 2 | **safe_blocked_patch (insufficient evidence criteria)** |
| `INVALID_STATUS_TRANSITION` | 1 | **unclassified_failure_requires_review** |
| `SUCCESS` | 4 | **recovery_patch_committed** |

## Final decision distribution

| decision | deepseek_full8 |
|---|---|
| `reject` | 8 |

