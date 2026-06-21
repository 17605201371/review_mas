# Run comparison dashboard v1

- candidate: `mimo_v25_route3_covgap_hardneg20_mt7_b4w2_api2_r8t600_20260620_110516.jsonl` (label: route3_covgap, papers: 20)
- baseline:  `mimo_v25_realneg_neg3gate_hardneg20_mt7_b4w4_api4_r8t600_20260620_011702.jsonl` (label: neg3gate_base, papers: 20)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 1 | **FAIL** |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `semantic_negative_without_review_relation_count` | `==` | 0 |  | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 101 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 97 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 75 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 48 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 2 | **FAIL** |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 70 | PASS |

**Overall protection: FAIL**

## Evidence formation health

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 81 | 76 | -5 |
| `evidence_json_status_turns` | 78 | 70 | -8 |
| `evidence_json_valid_turns` | 78 | 70 | -8 |
| `evidence_json_partial_recovered_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_rate_pct` | 0 | 0 | 0 |
| `evidence_json_no_json_object_turns` | 0 | 0 | 0 |
| `evidence_json_invalid_json_turns` | 0 | 0 | 0 |
| `evidence_json_truncated_turns` | 0 | 0 | 0 |
| `evidence_json_prompt_chars_median` | 7410 | 7410 | 0 |
| `evidence_json_raw_chars_median` | 2110 | 2086 | -24 |
| `quote_bank_nonzero_turns` | 81 | 76 | -5 |
| `payload_evidence_item_total` | 166 | 162 | -4 |
| `evidence_agent_nonempty_payload_turns` | 69 | 65 | -4 |
| `evidence_agent_question_only_turns` | 1 | 1 | 0 |
| `first_support_fallback_turns` | 0 | 1 | +1 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 43 | 52 | +9 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `real_strong_support_total` | 103 | 101 | -2 |
| `independent_support_group_total` | 97 | 97 | 0 |
| `diagnostic_independent_support_group_total` | 123 | 128 | +5 |
| `claims_with_2plus_independent_or_diagnostic_support` | 43 | 44 | +1 |
| `empirical_real_strong_support_count` | 71 | 75 | +4 |
| `method_real_strong_support_count` | 30 | 25 | -5 |
| `table_or_figure_real_strong_support_count` | 33 | 45 | +12 |
| `result_or_experiment_real_strong_support_count` | 33 | 26 | -7 |
| `ablation_real_strong_support_count` | 6 | 5 | -1 |
| `abstract_real_strong_support_count` | 1 | 0 | -1 |
| `verified_moderate_support_total` | 32 | 36 | +4 |
| `moderate_diagnostic_support_total` | 32 | 36 | +4 |
| `moderate_absorbed_into_final_strong_count` | 52 | 46 | -6 |
| `moderate_remaining_diagnostic_count` | 32 | 36 | +4 |
| `diagnostic_support_signal_total` | 135 | 137 | +2 |
| `papers_with_real_strong_support` | 20 | 20 | 0 |
| `papers_with_empirical_support` | 18 | 20 | +2 |
| `papers_with_deep_support` | 19 | 20 | +1 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 2 | 0 | -2 |
| `deep_support_gap_papers` | 1 | 0 | -1 |
| `claims_with_real_strong_support` | 52 | 56 | +4 |
| `claims_with_empirical_real_strong_support` | 39 | 46 | +7 |
| `claims_with_deep_support` | 46 | 48 | +2 |
| `claims_with_2plus_independent_support` | 34 | 33 | -1 |
| `primary_claim_total` | 60 | 60 | 0 |
| `primary_claims_with_real_strong_support` | 50 | 52 | +2 |
| `primary_claims_with_empirical_support` | 37 | 44 | +7 |
| `primary_claims_with_deep_support` | 44 | 46 | +2 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 103 | 101 | -2 |
| `final_support_direct_strong_count` | 51 | 54 | +3 |
| `final_support_promoted_from_medium_count` | 52 | 46 | -6 |
| `final_support_semantic_weak_promotion_count` | 0 | 1 | +1 |
| `near_miss_deep_moderate_support_count` | 4 | 3 | -1 |
| `near_miss_method_moderate_support_count` | 2 | 0 | -2 |
| `near_miss_specific_locator_moderate_count` | 4 | 1 | -3 |
| `near_miss_promoted_to_final_count` | 3 | 0 | -3 |
| `support_trace_total` | 196 | 202 | +6 |
| `support_trace_included_count` | 103 | 101 | -2 |
| `support_trace_dropped_count` | 93 | 101 | +8 |
| `support_trace_hygiene_filtered_count` | 24 | 30 | +6 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 34 | 39 | +5 |
| `support_trace_semantic_mismatch_count` | 18 | 22 | +4 |
| `support_trace_duplicate_quote_count` | 14 | 8 | -6 |
| `support_trace_missing_verified_quote_count` | 2 | 2 | 0 |
| `final_support_specific_locator_count` | 66 | 70 | +4 |
| `final_support_weak_locator_count` | 37 | 31 | -6 |

## Negative & flaws

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 0 | 1 | +1 |
| `review_negative_verified_count` | 0 | 1 | +1 |
| `paper_text_negative_candidate_count` | 7 | 13 | +6 |
| `author_limitation_only_count` | 0 | 0 | 0 |
| `prior_work_limitation_count` | 0 | 0 | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 | 0 | 0 |
| `semantic_negative_without_review_relation_count` | 2 | 0 | -2 |
| `scope_limitation_as_verified_negative_count` | 0 | 0 | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 0 | 1 | +1 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 0 | 1 | +1 |
| `verified_actionable_negative_flaw_count` | 0 | 1 | +1 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 0 | 1 | +1 |
| `negative_type_missing_ablation` | 1 | 0 | -1 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 1 | 0 | -1 |
| `negative_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `negative_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `negative_type_efficiency_cost_gap` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 1 | 0 | -1 |
| `negative_type_scope_limitation` | 0 | 0 | 0 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 2 | 0 | -2 |
| `verified_potential_concern_count` | 0 | 1 | +1 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 8 | 8 | 0 |
| `negative_grounding_conflict_count` | 1 | 1 | 0 |
| `invalid_negative_evidence_id_count_legacy` | 1 | 1 | 0 |
| `negative_semantic_anchor_conflict_count` | 1 | 1 | 0 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 1 | 1 | 0 |
| `downgraded_flaw_count` | 2 | 1 | -1 |
| `potential_concern_count` | 0 | 1 | +1 |
| `diagnosis_pending_potential_concern_count` | 68 | 58 | -10 |
| `diagnosis_pending_potential_concern_claim_count` | 43 | 40 | -3 |
| `diagnosis_pending_concern_recorded_count` | 0 | 0 | 0 |
| `diagnosis_pending_concern_recorded_claim_count` | 0 | 0 | 0 |
| `diagnosis_pending_type_missing_ablation` | 7 | 3 | -4 |
| `diagnosis_pending_type_missing_baseline` | 13 | 11 | -2 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 21 | 17 | -4 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 0 | 1 | +1 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `diagnosis_pending_type_efficiency_cost_gap` | 6 | 6 | 0 |
| `diagnosis_pending_type_reproducibility_gap` | 3 | 1 | -2 |
| `diagnosis_pending_type_scope_overclaim` | 3 | 5 | +2 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 | 0 | 0 |
| `diagnosis_pending_type_method_support_gap` | 15 | 14 | -1 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `verified_coverage_gap_count` | 16 | 12 | -4 |
| `primary_claims_with_requirement_gaps` | 30 | 30 | 0 |

## State contamination

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `state_contamination_count` | 1 | 1 | 0 |
| `state_contamination_count_legacy` | 1 | 1 | 0 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 1 | 1 | 0 |
| `state_hygiene_warning_count` | 1 | 1 | 0 |
| `weak_target_warning_count` | 1 | 1 | 0 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 1 | 1 | 0 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 0 | 0 |
| `contamination_stale_gap_persistence` | 0 | 0 | 0 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 1 | 1 | 0 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 1 | 1 | 0 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `contested_support_total` | 0 | 5 | +5 |
| `contested_final_support_total` | 0 | 3 | +3 |
| `claims_with_contested_support` | 0 | 1 | +1 |
| `claims_with_contested_final_support` | 0 | 1 | +1 |
| `open_conflict_count` | 21 | 33 | +12 |
| `contested_relation_final_count` | 0 | 0 | 0 |
| `contested_relation_added_count` | 0 | 0 | 0 |
| `contested_relation_effective_count` | 0 | 0 | 0 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 0 | 0 | 0 |
| `diagnosis_pending_concern_commit_count` | 0 | 0 | 0 |
| `diagnosis_pending_concern_added_count` | 0 | 0 | 0 |
| `mark_contested_commit_count` | 0 | 0 | 0 |
| `mark_contested_with_positive_support_count` | 0 | 0 | 0 |
| `mark_contested_with_verified_negative_evidence_count` | 0 | 0 | 0 |
| `mark_contested_final_view_count` | 0 | 0 | 0 |
| `contested_relation_with_positive_support_count` | 0 | 0 | 0 |
| `contested_relation_with_verified_negative_evidence_count` | 0 | 0 | 0 |
| `contested_relation_final_view_count` | 0 | 0 | 0 |

## Gap cleanup & locator

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 18 | 9 | -9 |
| `evidence_gap_resolved_count` | 59 | 66 | +7 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 2 | 3 | +1 |
| `state_hygiene_open_gap_count` | 18 | 9 | -9 |
| `state_hygiene_stale_gap_count` | 0 | 0 | 0 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 18 | 9 | -9 |
| `targeted_open_gap_count` | 18 | 9 | -9 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 46 | 47 | +1 |
| `unresolved_open_raw_count` | 172 | 171 | -1 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 169 | 164 | -5 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 66 | 70 | +4 |
| `programmatic_weak_locator_count` | 37 | 31 | -6 |
| `programmatic_locator_type_table_count` | 21 | 23 | +2 |
| `programmatic_locator_type_figure_count` | 16 | 21 | +5 |
| `programmatic_locator_type_section_count` | 25 | 24 | -1 |
| `programmatic_locator_type_algorithm_count` | 1 | 2 | +1 |
| `programmatic_locator_type_theorem_count` | 3 | 0 | -3 |
| `programmatic_locator_type_generic_count` | 37 | 31 | -6 |
| `programmatic_high_confidence_locator_count` | 65 | 69 | +4 |
| `programmatic_low_confidence_locator_count` | 1 | 1 | 0 |

## Recovery

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `recovery_attempted` | 9 | 8 | -1 |
| `recovery_patch_validated` | 1 | 1 | 0 |
| `recovery_patch_committed` | 0 | 1 | +1 |
| `recovery_committed` | 0 | 1 | +1 |
| `recovery_success` | 0 | 1 | +1 |
| `hygiene_delta_improved` | 0 | 0 | 0 |
| `diagnosis_pending_recorded_layer` | 0 | 0 | 0 |
| `recovery_effective_repair` | 0 | 0 | 0 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 3 | 6 | +3 |
| `recovery_safe_resolution_or_clean_state` | 20 | 20 | 0 |
| `hygiene_delta_or_safe_block` | 3 | 5 | +2 |
| `hygiene_delta_or_safe_block_or_clean_state` | 20 | 20 | 0 |
| `recovery_safe_blocked_weak_target` | 3 | 5 | +2 |
| `recovery_safe_blocked_terminal_target` | 0 | 0 | 0 |
| `recovery_terminal_turns` | 1 | 0 | -1 |
| `recovery_repeat_allowed_false_turns` | 1 | 0 | -1 |
| `recovery_target_gate_real_target_turns` | 1 | 1 | 0 |
| `recovery_target_gate_negative_verified_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_weak_target_turns` | 4 | 5 | +1 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 4 | 2 | -2 |
| `recovery_patch_operation_reject_patch_turns` | 9 | 7 | -2 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 | 1 | +1 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Recovery case audit

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `recovery_case_rows` | 10 | 9 | -1 |
| `recovery_case_audit_error_count` | 0 | 0 | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 | 0 | 0 |
| `recovery_case_verified_review_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_state_hygiene_repair` | 0 | 0 | 0 |
| `recovery_case_assessment_limitation_routing` | 0 | 0 | 0 |
| `recovery_case_effective_repair_without_verified_negative` | 0 | 0 | 0 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_attempted_not_committed` | 10 | 8 | -2 |
| `recovery_case_committed_not_effective` | 0 | 1 | +1 |
| `recovery_case_effective_repair_turns` | 0 | 0 | 0 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 0 | 0 | 0 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 | 1 | +1 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 | 1 | +1 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 0 | 1 | +1 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_support_only` | 3 | 0 | -3 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 | 2 | +2 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 | 1 | +1 |

## Hygiene

| metric | neg3gate_base | route3_covgap | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 1 | +1 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | neg3gate_base | route3_covgap | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 8 | 7 | -1 | **safe_blocked_patch (policy restriction/abstention)** |
| `NO_EFFECT_PATCH` | 1 | 0 | -1 | **safe_blocked_patch (no state change needed)** |
| `SUCCESS` | 0 | 1 | +1 | **recovery_patch_committed** |

## Final decision distribution

| decision | neg3gate_base | route3_covgap |
|---|---|---|
| `reject` | 20 | 20 |

