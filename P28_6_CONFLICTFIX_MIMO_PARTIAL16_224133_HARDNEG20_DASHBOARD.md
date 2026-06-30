# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260630_224133.jsonl` (label: P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133, papers: 16)
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
| `recovery_safe_resolution_or_clean_state` | `>=` | 9 | smoke scaled from 20/39 | 16 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 9 | smoke scaled from 20/39 | 15 | PASS |
| `real_strong_support_total` | `>=` | 13 | smoke scaled from 30/39 | 59 | PASS |
| `independent_support_group_total` | `>=` | 10 | smoke scaled from 24/39 | 56 | PASS |
| `empirical_real_strong_support_count` | `>=` | 9 | smoke scaled from 20/39 | 36 | PASS |
| `claims_with_deep_support` | `>=` | 4 | smoke scaled from 8/39 | 24 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 8 | smoke scaled from 18/39 | 36 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `evidence_agent_worker_turns` | 55 |
| `evidence_json_status_turns` | 51 |
| `evidence_json_valid_turns` | 51 |
| `evidence_json_partial_recovered_turns` | 0 |
| `evidence_json_fallback_turns` | 0 |
| `evidence_json_fallback_rate_pct` | 0 |
| `evidence_json_no_json_object_turns` | 0 |
| `evidence_json_invalid_json_turns` | 0 |
| `evidence_json_truncated_turns` | 0 |
| `evidence_json_prompt_chars_median` | 7826 |
| `evidence_json_raw_chars_median` | 2064 |
| `quote_bank_nonzero_turns` | 55 |
| `payload_evidence_item_total` | 104 |
| `evidence_agent_nonempty_payload_turns` | 40 |
| `evidence_agent_question_only_turns` | 0 |
| `first_support_fallback_turns` | 0 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 39 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `real_strong_support_total` | 59 |
| `independent_support_group_total` | 56 |
| `diagnostic_independent_support_group_total` | 69 |
| `claims_with_2plus_independent_or_diagnostic_support` | 23 |
| `empirical_real_strong_support_count` | 36 |
| `method_real_strong_support_count` | 23 |
| `table_or_figure_real_strong_support_count` | 22 |
| `result_or_experiment_real_strong_support_count` | 11 |
| `ablation_real_strong_support_count` | 3 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 14 |
| `moderate_diagnostic_support_total` | 14 |
| `moderate_absorbed_into_final_strong_count` | 32 |
| `moderate_remaining_diagnostic_count` | 14 |
| `diagnostic_support_signal_total` | 73 |
| `papers_with_real_strong_support` | 15 |
| `papers_with_empirical_support` | 13 |
| `papers_with_deep_support` | 13 |
| `positive_coverage_gap_papers` | 1 |
| `empirical_coverage_gap_papers` | 3 |
| `deep_support_gap_papers` | 3 |
| `claims_with_real_strong_support` | 37 |
| `claims_with_empirical_real_strong_support` | 23 |
| `claims_with_deep_support` | 24 |
| `claims_with_2plus_independent_support` | 16 |
| `primary_claim_total` | 48 |
| `primary_claims_with_real_strong_support` | 32 |
| `primary_claims_with_empirical_support` | 20 |
| `primary_claims_with_deep_support` | 21 |
| `zero_real_papers` | 1 |
| `final_support_total` | 59 |
| `final_support_direct_strong_count` | 27 |
| `final_support_promoted_from_medium_count` | 32 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 1 |
| `near_miss_method_moderate_support_count` | 1 |
| `near_miss_specific_locator_moderate_count` | 1 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 113 |
| `support_trace_included_count` | 59 |
| `support_trace_dropped_count` | 54 |
| `support_trace_hygiene_filtered_count` | 17 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 21 |
| `support_trace_semantic_mismatch_count` | 13 |
| `support_trace_duplicate_quote_count` | 3 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 36 |
| `final_support_weak_locator_count` | 23 |

## Negative & flaws

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `negative_evidence_candidate_count` | 12 |
| `negative_evidence_candidate_raw_count` | 12 |
| `review_negative_verified_count` | 0 |
| `reviewer_absence_verified_count` | 12 |
| `reviewer_absence_verified_claim_count` | 12 |
| `reviewer_absence_verified_flaw_count` | 12 |
| `total_review_negative_verified_count` | 12 |
| `quote_grounded_review_issue_count` | 0 |
| `obligation_grounded_review_issue_count` | 12 |
| `obligation_grounded_review_issue_claim_count` | 12 |
| `reviewer_candidate_review_issue_count` | 12 |
| `reviewer_candidate_review_issue_claim_count` | 12 |
| `reviewer_candidate_review_issue_critique_payload_count` | 0 |
| `reviewer_candidate_review_issue_deterministic_seed_count` | 12 |
| `reviewer_candidate_review_issue_other_candidate_count` | 0 |
| `claim_obligation_review_issue_count` | 0 |
| `claim_obligation_review_issue_claim_count` | 0 |
| `verified_review_issue_count` | 12 |
| `verified_review_issue_row_count` | 12 |
| `verified_review_issue_claim_count` | 12 |
| `review_issue_bundle_count` | 12 |
| `obligation_grounded_review_issue_cluster_count` | 8 |
| `reviewer_candidate_review_issue_cluster_count` | 8 |
| `claim_obligation_review_issue_cluster_count` | 0 |
| `verified_review_issue_cluster_count` | 8 |
| `duplicate_review_issue_row_count` | 4 |
| `verified_missing_ablation_cluster_count` | 6 |
| `verified_issue_without_recovery_count` | 7 |
| `verified_issue_cluster_without_recovery_count` | 3 |
| `review_issue_candidate_total` | 79 |
| `review_issue_candidate_verified` | 12 |
| `review_issue_candidate_retrieval_gap_rejected` | 0 |
| `review_issue_candidate_generic_item_rejected` | 8 |
| `review_issue_candidate_counterevidence_rejected` | 35 |
| `review_issue_candidate_missing_inventory_rejected` | 24 |
| `review_issue_candidate_off_claim_rejected` | 0 |
| `review_issue_candidate_review_worthiness_rejected` | 4 |
| `review_issue_candidate_missing_ablation_target_rejected` | 4 |
| `review_issue_candidate_missing_ablation_weak_action_rejected` | 2 |
| `review_issue_candidate_missing_ablation_generic_component_rejected` | 0 |
| `review_issue_candidate_missing_baseline_target_rejected` | 7 |
| `review_issue_candidate_missing_baseline_generic_target_rejected` | 7 |
| `verified_missing_ablation_high_confidence` | 7 |
| `verified_missing_ablation_medium_confidence` | 3 |
| `review_issue_type_missing_ablation` | 10 |
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
| `review_issue_cluster_type_missing_ablation` | 6 |
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
| `paper_text_negative_candidate_count` | 10 |
| `author_limitation_only_count` | 1 |
| `prior_work_limitation_count` | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 |
| `semantic_negative_without_review_relation_count` | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 |
| `scope_limitation_as_verified_negative_count` | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 |
| `negative_evidence_linked_to_flaw_count` | 12 |
| `negative_evidence_linked_to_flaw_raw_count` | 12 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 16 |
| `verified_actionable_negative_flaw_count` | 16 |
| `verified_limitation_negative_flaw_count` | 0 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 14 |
| `negative_type_missing_baseline` | 1 |
| `negative_type_unfair_or_weak_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 |
| `negative_type_evaluation_protocol_risk` | 0 |
| `negative_type_efficiency_cost_gap` | 0 |
| `negative_type_reproducibility_gap` | 1 |
| `negative_type_scope_overclaim` | 0 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 0 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 16 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 2 |
| `negative_grounding_conflict_count` | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 |
| `negative_semantic_anchor_conflict_count` | 0 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 3 |
| `downgraded_flaw_count` | 0 |
| `potential_concern_count` | 16 |
| `diagnosis_pending_potential_concern_count` | 93 |
| `diagnosis_pending_potential_concern_claim_count` | 40 |
| `diagnosis_pending_concern_recorded_count` | 0 |
| `diagnosis_pending_concern_recorded_claim_count` | 0 |
| `coverage_gap_potential_concern_count` | 20 |
| `reviewer_inferred_potential_concern_count` | 20 |
| `final_potential_concern_total` | 31 |
| `diagnosis_pending_type_missing_ablation` | 7 |
| `diagnosis_pending_type_missing_baseline` | 15 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 23 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 4 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 5 |
| `diagnosis_pending_type_efficiency_cost_gap` | 6 |
| `diagnosis_pending_type_reproducibility_gap` | 9 |
| `diagnosis_pending_type_scope_overclaim` | 9 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 |
| `diagnosis_pending_type_method_support_gap` | 15 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `verified_coverage_gap_count` | 20 |
| `coverage_gap_potential_concern_count` | 20 |
| `reviewer_inferred_potential_concern_count` | 20 |
| `final_potential_concern_total` | 31 |
| `primary_claims_with_requirement_gaps` | 30 |

## State contamination

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `state_contamination_count` | 7 |
| `state_contamination_count_legacy` | 7 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 7 |
| `state_hygiene_warning_count` | 7 |
| `weak_target_warning_count` | 7 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 7 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 1 |
| `contamination_stale_gap_persistence` | 5 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 0 |
| `contamination_meta_leakage` | 1 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 7 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `contested_support_total` | 18 |
| `contested_final_support_total` | 7 |
| `claims_with_contested_support` | 7 |
| `claims_with_contested_final_support` | 6 |
| `open_conflict_count` | 26 |
| `contested_relation_final_count` | 5 |
| `contested_relation_added_count` | 5 |
| `contested_relation_effective_count` | 5 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 2 |
| `diagnosis_pending_concern_commit_count` | 0 |
| `diagnosis_pending_concern_added_count` | 0 |
| `mark_contested_commit_count` | 5 |
| `mark_contested_with_positive_support_count` | 5 |
| `mark_contested_with_verified_negative_evidence_count` | 5 |
| `mark_contested_final_view_count` | 5 |
| `contested_relation_with_positive_support_count` | 5 |
| `contested_relation_with_verified_negative_evidence_count` | 5 |
| `contested_relation_final_view_count` | 5 |

## Gap cleanup & locator

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `evidence_gap_open_count` | 24 |
| `evidence_gap_resolved_count` | 41 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 1 |
| `state_hygiene_open_gap_count` | 18 |
| `state_hygiene_stale_gap_count` | 6 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 2 |
| `diagnostic_targeted_open_gap_count` | 22 |
| `targeted_open_gap_count` | 24 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 42 |
| `unresolved_open_raw_count` | 137 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 134 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 36 |
| `programmatic_weak_locator_count` | 23 |
| `programmatic_locator_type_table_count` | 5 |
| `programmatic_locator_type_figure_count` | 17 |
| `programmatic_locator_type_section_count` | 14 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 23 |
| `programmatic_high_confidence_locator_count` | 36 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `recovery_attempted` | 13 |
| `recovery_patch_validated` | 6 |
| `recovery_patch_committed` | 6 |
| `recovery_committed` | 6 |
| `recovery_success` | 6 |
| `hygiene_delta_improved` | 5 |
| `diagnosis_pending_recorded_layer` | 0 |
| `recovery_effective_repair` | 5 |
| `recovery_no_effect_commit` | 1 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_harmful_commit_committed` | 0 |
| `recovery_unsafe_downgrade_attempt_blocked` | 2 |
| `recovery_safe_resolution` | 11 |
| `recovery_safe_resolution_or_clean_state` | 16 |
| `hygiene_delta_or_safe_block` | 10 |
| `hygiene_delta_or_safe_block_or_clean_state` | 15 |
| `recovery_safe_blocked_weak_target` | 3 |
| `recovery_safe_blocked_terminal_target` | 2 |
| `recovery_terminal_turns` | 2 |
| `recovery_repeat_allowed_false_turns` | 2 |
| `recovery_target_gate_real_target_turns` | 6 |
| `recovery_target_gate_negative_verified_target_turns` | 2 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 0 |
| `recovery_target_gate_weak_target_turns` | 4 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 1 |
| `recovery_patch_operation_reject_patch_turns` | 7 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 1 |
| `recovery_patch_operation_mark_contested_turns` | 5 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Recovery case audit

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `recovery_case_rows` | 17 |
| `recovery_case_audit_error_count` | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 |
| `recovery_case_verified_review_negative_repair` | 0 |
| `recovery_case_verified_review_issue_repair` | 5 |
| `verified_issue_contested_repair` | 5 |
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
| `recovery_case_attempted_not_committed` | 11 |
| `recovery_case_committed_not_effective` | 1 |
| `recovery_case_effective_repair_turns` | 5 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 5 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 6 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 6 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 |
| `recovery_case_evidence_bucket_stale_reviewer_absence_audit` | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 1 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 |

## Hygiene

| metric | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 | interpreted safety outcome |
|---|---|---|
| `BLOCKED_BY_POLICY` | 6 | **safe_blocked_patch (policy restriction/abstention)** |
| `SUCCESS` | 6 | **recovery_patch_committed** |
| `UNKNOWN_TARGET` | 1 | **unclassified_failure_requires_review** |

## Final decision distribution

| decision | P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133 |
|---|---|
| `reject` | 16 |
