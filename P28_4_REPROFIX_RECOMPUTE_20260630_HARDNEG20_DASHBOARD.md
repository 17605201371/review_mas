# Run comparison dashboard v1

- candidate: `P28_3_PROMPTDISC_COMBINED_20260630_013639_104423_HARDNEG20.jsonl` (label: P28_4_REPROFIX_RECOMPUTE_20260630, papers: 20)
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
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 17 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 16 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 79 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 74 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 54 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 39 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 57 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `evidence_agent_worker_turns` | 75 |
| `evidence_json_status_turns` | 70 |
| `evidence_json_valid_turns` | 70 |
| `evidence_json_partial_recovered_turns` | 0 |
| `evidence_json_fallback_turns` | 0 |
| `evidence_json_fallback_rate_pct` | 0 |
| `evidence_json_no_json_object_turns` | 0 |
| `evidence_json_invalid_json_turns` | 0 |
| `evidence_json_truncated_turns` | 0 |
| `evidence_json_prompt_chars_median` | 7826 |
| `evidence_json_raw_chars_median` | 1811 |
| `quote_bank_nonzero_turns` | 75 |
| `payload_evidence_item_total` | 145 |
| `evidence_agent_nonempty_payload_turns` | 58 |
| `evidence_agent_question_only_turns` | 0 |
| `first_support_fallback_turns` | 4 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 51 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `real_strong_support_total` | 79 |
| `independent_support_group_total` | 74 |
| `diagnostic_independent_support_group_total` | 98 |
| `claims_with_2plus_independent_or_diagnostic_support` | 34 |
| `empirical_real_strong_support_count` | 54 |
| `method_real_strong_support_count` | 25 |
| `table_or_figure_real_strong_support_count` | 40 |
| `result_or_experiment_real_strong_support_count` | 9 |
| `ablation_real_strong_support_count` | 5 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 27 |
| `moderate_diagnostic_support_total` | 27 |
| `moderate_absorbed_into_final_strong_count` | 46 |
| `moderate_remaining_diagnostic_count` | 27 |
| `diagnostic_support_signal_total` | 106 |
| `papers_with_real_strong_support` | 19 |
| `papers_with_empirical_support` | 17 |
| `papers_with_deep_support` | 17 |
| `positive_coverage_gap_papers` | 1 |
| `empirical_coverage_gap_papers` | 3 |
| `deep_support_gap_papers` | 3 |
| `claims_with_real_strong_support` | 49 |
| `claims_with_empirical_real_strong_support` | 36 |
| `claims_with_deep_support` | 39 |
| `claims_with_2plus_independent_support` | 22 |
| `primary_claim_total` | 58 |
| `primary_claims_with_real_strong_support` | 42 |
| `primary_claims_with_empirical_support` | 30 |
| `primary_claims_with_deep_support` | 33 |
| `zero_real_papers` | 1 |
| `final_support_total` | 79 |
| `final_support_direct_strong_count` | 33 |
| `final_support_promoted_from_medium_count` | 46 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 3 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 2 |
| `near_miss_promoted_to_final_count` | 1 |
| `support_trace_total` | 145 |
| `support_trace_included_count` | 79 |
| `support_trace_dropped_count` | 66 |
| `support_trace_hygiene_filtered_count` | 29 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 19 |
| `support_trace_semantic_mismatch_count` | 13 |
| `support_trace_duplicate_quote_count` | 3 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 57 |
| `final_support_weak_locator_count` | 22 |

## Negative & flaws

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `negative_evidence_candidate_count` | 11 |
| `negative_evidence_candidate_raw_count` | 11 |
| `review_negative_verified_count` | 1 |
| `reviewer_absence_verified_count` | 10 |
| `reviewer_absence_verified_claim_count` | 14 |
| `reviewer_absence_verified_flaw_count` | 10 |
| `total_review_negative_verified_count` | 11 |
| `quote_grounded_review_issue_count` | 1 |
| `obligation_grounded_review_issue_count` | 10 |
| `obligation_grounded_review_issue_claim_count` | 10 |
| `reviewer_candidate_review_issue_count` | 10 |
| `reviewer_candidate_review_issue_claim_count` | 10 |
| `claim_obligation_review_issue_count` | 0 |
| `claim_obligation_review_issue_claim_count` | 0 |
| `verified_review_issue_count` | 11 |
| `verified_review_issue_row_count` | 11 |
| `verified_review_issue_claim_count` | 11 |
| `review_issue_bundle_count` | 10 |
| `obligation_grounded_review_issue_cluster_count` | 7 |
| `reviewer_candidate_review_issue_cluster_count` | 7 |
| `claim_obligation_review_issue_cluster_count` | 0 |
| `verified_review_issue_cluster_count` | 8 |
| `duplicate_review_issue_row_count` | 3 |
| `verified_missing_ablation_cluster_count` | 5 |
| `verified_issue_without_recovery_count` | 7 |
| `verified_issue_cluster_without_recovery_count` | 5 |
| `review_issue_candidate_total` | 82 |
| `review_issue_candidate_verified` | 10 |
| `review_issue_candidate_retrieval_gap_rejected` | 0 |
| `review_issue_candidate_generic_item_rejected` | 10 |
| `review_issue_candidate_counterevidence_rejected` | 33 |
| `review_issue_candidate_missing_inventory_rejected` | 22 |
| `review_issue_candidate_off_claim_rejected` | 0 |
| `review_issue_candidate_review_worthiness_rejected` | 8 |
| `review_issue_candidate_missing_ablation_target_rejected` | 7 |
| `review_issue_candidate_missing_ablation_weak_action_rejected` | 0 |
| `review_issue_candidate_missing_ablation_generic_component_rejected` | 0 |
| `review_issue_candidate_missing_baseline_target_rejected` | 10 |
| `review_issue_candidate_missing_baseline_generic_target_rejected` | 10 |
| `verified_missing_ablation_high_confidence` | 6 |
| `verified_missing_ablation_medium_confidence` | 2 |
| `review_issue_type_missing_ablation` | 8 |
| `review_issue_type_missing_baseline` | 1 |
| `review_issue_type_unfair_or_weak_baseline` | 0 |
| `review_issue_type_insufficient_evaluation` | 0 |
| `review_issue_type_missing_robustness_or_generalization` | 0 |
| `review_issue_type_evaluation_protocol_risk` | 0 |
| `review_issue_type_efficiency_cost_gap` | 0 |
| `review_issue_type_scope_overclaim` | 0 |
| `review_issue_type_result_claim_mismatch` | 0 |
| `review_issue_type_method_support_gap` | 0 |
| `review_issue_type_reproducibility_gap` | 1 |
| `review_issue_cluster_type_missing_ablation` | 5 |
| `review_issue_cluster_type_missing_baseline` | 1 |
| `review_issue_cluster_type_unfair_or_weak_baseline` | 0 |
| `review_issue_cluster_type_insufficient_evaluation` | 0 |
| `review_issue_cluster_type_missing_robustness_or_generalization` | 0 |
| `review_issue_cluster_type_evaluation_protocol_risk` | 0 |
| `review_issue_cluster_type_efficiency_cost_gap` | 0 |
| `review_issue_cluster_type_scope_overclaim` | 0 |
| `review_issue_cluster_type_result_claim_mismatch` | 0 |
| `review_issue_cluster_type_method_support_gap` | 0 |
| `review_issue_cluster_type_reproducibility_gap` | 1 |
| `paper_text_negative_candidate_count` | 18 |
| `author_limitation_only_count` | 0 |
| `prior_work_limitation_count` | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 |
| `semantic_negative_without_review_relation_count` | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 |
| `scope_limitation_as_verified_negative_count` | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 |
| `negative_evidence_linked_to_flaw_count` | 11 |
| `negative_evidence_linked_to_flaw_raw_count` | 11 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 12 |
| `verified_actionable_negative_flaw_count` | 12 |
| `verified_limitation_negative_flaw_count` | 0 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 10 |
| `negative_type_missing_baseline` | 1 |
| `negative_type_unfair_or_weak_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 |
| `negative_type_evaluation_protocol_risk` | 1 |
| `negative_type_efficiency_cost_gap` | 0 |
| `negative_type_reproducibility_gap` | 1 |
| `negative_type_scope_overclaim` | 0 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 0 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 12 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 14 |
| `negative_grounding_conflict_count` | 9 |
| `invalid_negative_evidence_id_count_legacy` | 9 |
| `negative_semantic_anchor_conflict_count` | 9 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 0 |
| `downgraded_flaw_count` | 1 |
| `potential_concern_count` | 12 |
| `diagnosis_pending_potential_concern_count` | 91 |
| `diagnosis_pending_potential_concern_claim_count` | 45 |
| `diagnosis_pending_concern_recorded_count` | 3 |
| `diagnosis_pending_concern_recorded_claim_count` | 3 |
| `coverage_gap_potential_concern_count` | 20 |
| `reviewer_inferred_potential_concern_count` | 20 |
| `final_potential_concern_total` | 27 |
| `diagnosis_pending_type_missing_ablation` | 9 |
| `diagnosis_pending_type_missing_baseline` | 17 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 18 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 2 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 6 |
| `diagnosis_pending_type_efficiency_cost_gap` | 7 |
| `diagnosis_pending_type_reproducibility_gap` | 9 |
| `diagnosis_pending_type_scope_overclaim` | 10 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 |
| `diagnosis_pending_type_method_support_gap` | 13 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `verified_coverage_gap_count` | 20 |
| `coverage_gap_potential_concern_count` | 20 |
| `reviewer_inferred_potential_concern_count` | 20 |
| `final_potential_concern_total` | 27 |
| `primary_claims_with_requirement_gaps` | 36 |

## State contamination

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `state_contamination_count` | 11 |
| `state_contamination_count_legacy` | 11 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 11 |
| `state_hygiene_warning_count` | 11 |
| `weak_target_warning_count` | 11 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 11 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 1 |
| `contamination_stale_gap_persistence` | 1 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 9 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 11 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `contested_support_total` | 28 |
| `contested_final_support_total` | 12 |
| `claims_with_contested_support` | 10 |
| `claims_with_contested_final_support` | 9 |
| `open_conflict_count` | 38 |
| `contested_relation_final_count` | 3 |
| `contested_relation_added_count` | 4 |
| `contested_relation_effective_count` | 3 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 3 |
| `diagnosis_pending_concern_commit_count` | 3 |
| `diagnosis_pending_concern_added_count` | 3 |
| `mark_contested_commit_count` | 4 |
| `mark_contested_with_positive_support_count` | 4 |
| `mark_contested_with_verified_negative_evidence_count` | 4 |
| `mark_contested_final_view_count` | 4 |
| `contested_relation_with_positive_support_count` | 3 |
| `contested_relation_with_verified_negative_evidence_count` | 3 |
| `contested_relation_final_view_count` | 3 |

## Gap cleanup & locator

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `evidence_gap_open_count` | 17 |
| `evidence_gap_resolved_count` | 57 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 1 |
| `state_hygiene_open_gap_count` | 15 |
| `state_hygiene_stale_gap_count` | 2 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 17 |
| `targeted_open_gap_count` | 17 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 53 |
| `unresolved_open_raw_count` | 155 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 147 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 57 |
| `programmatic_weak_locator_count` | 22 |
| `programmatic_locator_type_table_count` | 20 |
| `programmatic_locator_type_figure_count` | 18 |
| `programmatic_locator_type_section_count` | 17 |
| `programmatic_locator_type_algorithm_count` | 2 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 22 |
| `programmatic_high_confidence_locator_count` | 57 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `recovery_attempted` | 14 |
| `recovery_patch_validated` | 10 |
| `recovery_patch_committed` | 10 |
| `recovery_committed` | 10 |
| `recovery_success` | 10 |
| `hygiene_delta_improved` | 4 |
| `diagnosis_pending_recorded_layer` | 3 |
| `recovery_effective_repair` | 4 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 1 |
| `recovery_safe_resolution` | 14 |
| `recovery_safe_resolution_or_clean_state` | 17 |
| `hygiene_delta_or_safe_block` | 8 |
| `hygiene_delta_or_safe_block_or_clean_state` | 16 |
| `recovery_safe_blocked_weak_target` | 1 |
| `recovery_safe_blocked_terminal_target` | 3 |
| `recovery_terminal_turns` | 3 |
| `recovery_repeat_allowed_false_turns` | 3 |
| `recovery_target_gate_real_target_turns` | 7 |
| `recovery_target_gate_negative_verified_target_turns` | 3 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 3 |
| `recovery_target_gate_weak_target_turns` | 1 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 4 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 3 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 4 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 3 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Recovery case audit

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `recovery_case_rows` | 16 |
| `recovery_case_audit_error_count` | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 |
| `recovery_case_verified_review_negative_repair` | 0 |
| `recovery_case_verified_review_issue_repair` | 4 |
| `verified_issue_contested_repair` | 4 |
| `stale_absence_contested_repair` | 0 |
| `recovery_case_reviewer_inferred_negative_repair` | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 |
| `recovery_case_verified_review_issue_lifecycle_downgrade` | 0 |
| `recovery_case_reviewer_inferred_flaw_lifecycle_downgrade` | 0 |
| `recovery_case_state_hygiene_repair` | 0 |
| `recovery_case_assessment_limitation_routing` | 0 |
| `recovery_case_effective_repair_without_verified_negative` | 0 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 |
| `recovery_case_attempted_not_committed` | 6 |
| `recovery_case_committed_not_effective` | 6 |
| `recovery_case_effective_repair_turns` | 4 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 4 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 1 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 4 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 1 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 4 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 |
| `recovery_case_evidence_bucket_stale_reviewer_absence_audit` | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 2 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 |
| `recovery_case_evidence_bucket_support_only` | 1 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 |

## Hygiene

| metric | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | P28_4_REPROFIX_RECOMPUTE_20260630 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 4 | **safe_blocked_patch (policy restriction/abstention)** |
| `SUCCESS` | 10 | **recovery_patch_committed** |

## Final decision distribution

| decision | P28_4_REPROFIX_RECOMPUTE_20260630 |
|---|---|
| `reject` | 20 |

