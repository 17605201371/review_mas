# Run comparison dashboard v1

- candidate: `mimo_v25_contextfix_targetneg_hardneg20_mt7_b4w2_api2_r5plus8t600_20260625_200722_MERGED20.jsonl` (label: contextfix_targetneg_merged20, papers: 20)
- baseline:  `mimo_v25_tablescopefix_hardneg20_mt7_b4w2_api2_r5t600_20260622_214828.jsonl` (label: tablescopefix, papers: 20)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `semantic_negative_without_review_relation_count` | `==` | 0 |  | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 15 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 15 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 63 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 62 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 43 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 30 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 42 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 80 | 67 | -13 |
| `evidence_json_status_turns` | 77 | 64 | -13 |
| `evidence_json_valid_turns` | 77 | 43 | -34 |
| `evidence_json_partial_recovered_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_turns` | 0 | 21 | +21 |
| `evidence_json_fallback_rate_pct` | 0 | 33 | +33 |
| `evidence_json_no_json_object_turns` | 0 | 12 | +12 |
| `evidence_json_invalid_json_turns` | 0 | 6 | +6 |
| `evidence_json_truncated_turns` | 0 | 3 | +3 |
| `evidence_json_prompt_chars_median` | 7826 | 7826 | 0 |
| `evidence_json_raw_chars_median` | 2181 | 2595 | +414 |
| `quote_bank_nonzero_turns` | 80 | 65 | -15 |
| `payload_evidence_item_total` | 134 | 113 | -21 |
| `evidence_agent_nonempty_payload_turns` | 74 | 52 | -22 |
| `evidence_agent_question_only_turns` | 22 | 4 | -18 |
| `first_support_fallback_turns` | 0 | 17 | +17 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 46 | 45 | -1 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `real_strong_support_total` | 76 | 63 | -13 |
| `independent_support_group_total` | 76 | 62 | -14 |
| `diagnostic_independent_support_group_total` | 96 | 73 | -23 |
| `claims_with_2plus_independent_or_diagnostic_support` | 35 | 30 | -5 |
| `empirical_real_strong_support_count` | 55 | 43 | -12 |
| `method_real_strong_support_count` | 20 | 18 | -2 |
| `table_or_figure_real_strong_support_count` | 34 | 26 | -8 |
| `result_or_experiment_real_strong_support_count` | 16 | 17 | +1 |
| `ablation_real_strong_support_count` | 6 | 2 | -4 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 21 | 14 | -7 |
| `moderate_diagnostic_support_total` | 21 | 14 | -7 |
| `moderate_absorbed_into_final_strong_count` | 47 | 38 | -9 |
| `moderate_remaining_diagnostic_count` | 21 | 14 | -7 |
| `diagnostic_support_signal_total` | 97 | 77 | -20 |
| `papers_with_real_strong_support` | 20 | 15 | -5 |
| `papers_with_empirical_support` | 18 | 13 | -5 |
| `papers_with_deep_support` | 18 | 14 | -4 |
| `positive_coverage_gap_papers` | 0 | 5 | +5 |
| `empirical_coverage_gap_papers` | 2 | 7 | +5 |
| `deep_support_gap_papers` | 2 | 6 | +4 |
| `claims_with_real_strong_support` | 48 | 36 | -12 |
| `claims_with_empirical_real_strong_support` | 36 | 26 | -10 |
| `claims_with_deep_support` | 39 | 30 | -9 |
| `claims_with_2plus_independent_support` | 24 | 23 | -1 |
| `primary_claim_total` | 60 | 43 | -17 |
| `primary_claims_with_real_strong_support` | 45 | 35 | -10 |
| `primary_claims_with_empirical_support` | 33 | 25 | -8 |
| `primary_claims_with_deep_support` | 36 | 29 | -7 |
| `zero_real_papers` | 0 | 5 | +5 |
| `final_support_total` | 76 | 63 | -13 |
| `final_support_direct_strong_count` | 28 | 25 | -3 |
| `final_support_promoted_from_medium_count` | 47 | 38 | -9 |
| `final_support_semantic_weak_promotion_count` | 1 | 0 | -1 |
| `near_miss_deep_moderate_support_count` | 2 | 0 | -2 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 2 | 0 | -2 |
| `near_miss_promoted_to_final_count` | 1 | 0 | -1 |
| `support_trace_total` | 166 | 110 | -56 |
| `support_trace_included_count` | 76 | 63 | -13 |
| `support_trace_dropped_count` | 90 | 47 | -43 |
| `support_trace_hygiene_filtered_count` | 27 | 15 | -12 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 29 | 9 | -20 |
| `support_trace_semantic_mismatch_count` | 23 | 1 | -22 |
| `support_trace_duplicate_quote_count` | 7 | 4 | -3 |
| `support_trace_missing_verified_quote_count` | 3 | 0 | -3 |
| `final_support_specific_locator_count` | 54 | 42 | -12 |
| `final_support_weak_locator_count` | 22 | 21 | -1 |

## Negative & flaws

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 0 | 0 | 0 |
| `review_negative_verified_count` | 0 | 0 | 0 |
| `paper_text_negative_candidate_count` | 15 | 4 | -11 |
| `author_limitation_only_count` | 0 | 0 | 0 |
| `prior_work_limitation_count` | 0 | 0 | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 | 0 | 0 |
| `semantic_negative_without_review_relation_count` | 0 | 0 | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 | 1 | 0 |
| `scope_limitation_as_verified_negative_count` | 0 | 0 | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 0 | 0 | 0 |
| `verified_actionable_negative_flaw_count` | 0 | 0 | 0 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 1 | 2 | +1 |
| `negative_type_missing_ablation` | 0 | 0 | 0 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 1 | 1 | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `negative_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `negative_type_efficiency_cost_gap` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 1 | +1 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 2 | 1 | -1 |
| `verified_potential_concern_count` | 0 | 0 | 0 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 8 | 7 | -1 |
| `negative_grounding_conflict_count` | 2 | 1 | -1 |
| `invalid_negative_evidence_id_count_legacy` | 2 | 1 | -1 |
| `negative_semantic_anchor_conflict_count` | 2 | 1 | -1 |
| `generic_gap_semantic_rejected_count` | 2 | 0 | -2 |
| `negative_evidence_semantic_rejected_count` | 2 | 0 | -2 |
| `downgraded_flaw_count` | 2 | 1 | -1 |
| `potential_concern_count` | 0 | 0 | 0 |
| `diagnosis_pending_potential_concern_count` | 74 | 52 | -22 |
| `diagnosis_pending_potential_concern_claim_count` | 45 | 30 | -15 |
| `diagnosis_pending_concern_recorded_count` | 0 | 0 | 0 |
| `diagnosis_pending_concern_recorded_claim_count` | 0 | 0 | 0 |
| `coverage_gap_potential_concern_count` | 17 | 12 | -5 |
| `reviewer_inferred_potential_concern_count` | 17 | 12 | -5 |
| `final_potential_concern_total` | 17 | 12 | -5 |
| `diagnosis_pending_type_missing_ablation` | 9 | 5 | -4 |
| `diagnosis_pending_type_missing_baseline` | 15 | 12 | -3 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 22 | 17 | -5 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 1 | 4 | +3 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `diagnosis_pending_type_efficiency_cost_gap` | 3 | 2 | -1 |
| `diagnosis_pending_type_reproducibility_gap` | 2 | 0 | -2 |
| `diagnosis_pending_type_scope_overclaim` | 5 | 4 | -1 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 | 0 | 0 |
| `diagnosis_pending_type_method_support_gap` | 17 | 8 | -9 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `verified_coverage_gap_count` | 17 | 12 | -5 |
| `coverage_gap_potential_concern_count` | 17 | 12 | -5 |
| `reviewer_inferred_potential_concern_count` | 17 | 12 | -5 |
| `final_potential_concern_total` | 17 | 12 | -5 |
| `primary_claims_with_requirement_gaps` | 36 | 23 | -13 |

## State contamination

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `state_contamination_count` | 2 | 7 | +5 |
| `state_contamination_count_legacy` | 2 | 7 | +5 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 1 | +1 |
| `conservative_state_warning_count` | 2 | 6 | +4 |
| `state_hygiene_warning_count` | 2 | 6 | +4 |
| `weak_target_warning_count` | 2 | 6 | +4 |
| `repairable_contamination_target_count` | 0 | 1 | +1 |
| `conservative_contamination_target_count` | 2 | 6 | +4 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 5 | +5 |
| `contamination_stale_gap_persistence` | 0 | 0 | 0 |
| `contamination_unsupported_flaw_escalation` | 0 | 1 | +1 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 2 | 1 | -1 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 1 | +1 |
| `target_gate_weak_target` | 2 | 6 | +4 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `contested_support_total` | 0 | 0 | 0 |
| `contested_final_support_total` | 0 | 0 | 0 |
| `claims_with_contested_support` | 0 | 0 | 0 |
| `claims_with_contested_final_support` | 0 | 0 | 0 |
| `open_conflict_count` | 31 | 11 | -20 |
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

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 14 | 15 | +1 |
| `evidence_gap_resolved_count` | 58 | 44 | -14 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 2 | 14 | +12 |
| `state_hygiene_open_gap_count` | 14 | 14 | 0 |
| `state_hygiene_stale_gap_count` | 0 | 1 | +1 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 14 | 15 | +1 |
| `targeted_open_gap_count` | 14 | 15 | +1 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 50 | 31 | -19 |
| `unresolved_open_raw_count` | 171 | 74 | -97 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 166 | 73 | -93 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 54 | 42 | -12 |
| `programmatic_weak_locator_count` | 22 | 21 | -1 |
| `programmatic_locator_type_table_count` | 16 | 11 | -5 |
| `programmatic_locator_type_figure_count` | 17 | 15 | -2 |
| `programmatic_locator_type_section_count` | 19 | 13 | -6 |
| `programmatic_locator_type_algorithm_count` | 1 | 2 | +1 |
| `programmatic_locator_type_theorem_count` | 1 | 1 | 0 |
| `programmatic_locator_type_generic_count` | 22 | 21 | -1 |
| `programmatic_high_confidence_locator_count` | 53 | 42 | -11 |
| `programmatic_low_confidence_locator_count` | 1 | 0 | -1 |

## Recovery

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `recovery_attempted` | 4 | 5 | +1 |
| `recovery_patch_validated` | 1 | 0 | -1 |
| `recovery_patch_committed` | 0 | 0 | 0 |
| `recovery_committed` | 0 | 0 | 0 |
| `recovery_success` | 0 | 0 | 0 |
| `hygiene_delta_improved` | 0 | 0 | 0 |
| `diagnosis_pending_recorded_layer` | 0 | 0 | 0 |
| `recovery_effective_repair` | 0 | 0 | 0 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 2 | 1 | -1 |
| `recovery_safe_resolution_or_clean_state` | 19 | 15 | -4 |
| `hygiene_delta_or_safe_block` | 2 | 1 | -1 |
| `hygiene_delta_or_safe_block_or_clean_state` | 19 | 15 | -4 |
| `recovery_safe_blocked_weak_target` | 2 | 1 | -1 |
| `recovery_safe_blocked_terminal_target` | 0 | 0 | 0 |
| `recovery_terminal_turns` | 0 | 1 | +1 |
| `recovery_repeat_allowed_false_turns` | 0 | 1 | +1 |
| `recovery_target_gate_real_target_turns` | 0 | 1 | +1 |
| `recovery_target_gate_negative_verified_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_weak_target_turns` | 3 | 1 | -2 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 1 | 3 | +2 |
| `recovery_patch_operation_reject_patch_turns` | 4 | 5 | +1 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Recovery case audit

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `recovery_case_rows` | 7 | 5 | -2 |
| `recovery_case_audit_error_count` | 0 | 0 | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 | 0 | 0 |
| `recovery_case_verified_review_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_state_hygiene_repair` | 0 | 0 | 0 |
| `recovery_case_assessment_limitation_routing` | 0 | 0 | 0 |
| `recovery_case_effective_repair_without_verified_negative` | 0 | 0 | 0 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_attempted_not_committed` | 7 | 5 | -2 |
| `recovery_case_committed_not_effective` | 0 | 0 | 0 |
| `recovery_case_effective_repair_turns` | 0 | 0 | 0 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 0 | 0 | 0 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 1 | 0 | -1 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 | 0 | 0 |

## Hygiene

| metric | tablescopefix | contextfix_targetneg_merged20 | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 1 | 0 | -1 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | tablescopefix | contextfix_targetneg_merged20 | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 3 | 5 | +2 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_TARGET_MISMATCH` | 1 | 0 | -1 | **safe_blocked_patch (missing or unverified IDs)** |

## Final decision distribution

| decision | tablescopefix | contextfix_targetneg_merged20 |
|---|---|---|
| `reject` | 20 | 20 |

