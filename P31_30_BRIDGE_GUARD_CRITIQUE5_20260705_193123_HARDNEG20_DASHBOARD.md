# Run comparison dashboard v1

- candidate: `p31_30_bridge_guard_critique5_20260705_193123.jsonl` (label: P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123, papers: 5)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `negative_grounding_conflict_count` | `==` | 0 |  | 0 | PASS |
| `semantic_negative_without_review_relation_count` | `==` | 0 |  | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | `==` | 0 |  | 0 | PASS |
| `recovery_harmful_commit_committed` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 3 | smoke scaled from 20/39 | 5 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 3 | smoke scaled from 20/39 | 5 | PASS |
| `real_strong_support_total` | `>=` | 4 | smoke scaled from 30/39 | 13 | PASS |
| `independent_support_group_total` | `>=` | 4 | smoke scaled from 24/39 | 13 | PASS |
| `empirical_real_strong_support_count` | `>=` | 3 | smoke scaled from 20/39 | 6 | PASS |
| `claims_with_deep_support` | `>=` | 2 | smoke scaled from 8/39 | 5 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 3 | smoke scaled from 18/39 | 10 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `evidence_agent_worker_turns` | 16 |
| `evidence_json_status_turns` | 15 |
| `evidence_json_valid_turns` | 15 |
| `evidence_json_partial_recovered_turns` | 0 |
| `evidence_json_fallback_turns` | 0 |
| `evidence_json_fallback_rate_pct` | 0 |
| `evidence_json_no_json_object_turns` | 0 |
| `evidence_json_invalid_json_turns` | 0 |
| `evidence_json_truncated_turns` | 0 |
| `evidence_json_prompt_chars_median` | 7826 |
| `evidence_json_raw_chars_median` | 1252 |
| `critique_worker_turns` | 18 |
| `review_issue_selected_menu_recovery_turns` | 5 |
| `review_issue_selected_menu_recovered_count` | 5 |
| `review_issue_seed_topup_turns` | 1 |
| `review_issue_seed_topup_candidate_count` | 1 |
| `seed_topup_after_critique_failure_count` | 1 |
| `review_issue_seed_topup_shadowed_by_existing_cluster_count` | 1 |
| `critique_only_seed_skipped_turns` | 0 |
| `critique_prompt_chars_median` | 10909 |
| `critique_prompt_chars_max` | 11673 |
| `critique_prompt_over_15k_turns` | 0 |
| `critique_prompt_over_30k_turns` | 0 |
| `quote_bank_nonzero_turns` | 16 |
| `payload_evidence_item_total` | 20 |
| `evidence_agent_nonempty_payload_turns` | 10 |
| `evidence_agent_question_only_turns` | 0 |
| `first_support_fallback_turns` | 1 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 8 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `real_strong_support_total` | 13 |
| `independent_support_group_total` | 13 |
| `diagnostic_independent_support_group_total` | 14 |
| `claims_with_2plus_independent_or_diagnostic_support` | 5 |
| `empirical_real_strong_support_count` | 6 |
| `method_real_strong_support_count` | 7 |
| `table_or_figure_real_strong_support_count` | 3 |
| `result_or_experiment_real_strong_support_count` | 2 |
| `ablation_real_strong_support_count` | 1 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 1 |
| `moderate_diagnostic_support_total` | 1 |
| `moderate_absorbed_into_final_strong_count` | 7 |
| `moderate_remaining_diagnostic_count` | 1 |
| `diagnostic_support_signal_total` | 14 |
| `papers_with_real_strong_support` | 5 |
| `papers_with_empirical_support` | 3 |
| `papers_with_deep_support` | 4 |
| `positive_coverage_gap_papers` | 0 |
| `empirical_coverage_gap_papers` | 2 |
| `deep_support_gap_papers` | 1 |
| `claims_with_real_strong_support` | 8 |
| `claims_with_empirical_real_strong_support` | 4 |
| `claims_with_deep_support` | 5 |
| `claims_with_2plus_independent_support` | 4 |
| `primary_claim_total` | 15 |
| `primary_claims_with_real_strong_support` | 8 |
| `primary_claims_with_empirical_support` | 4 |
| `primary_claims_with_deep_support` | 5 |
| `zero_real_papers` | 0 |
| `final_support_total` | 13 |
| `final_support_direct_strong_count` | 6 |
| `final_support_promoted_from_medium_count` | 7 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 0 |
| `near_miss_method_moderate_support_count` | 1 |
| `near_miss_specific_locator_moderate_count` | 1 |
| `near_miss_promoted_to_final_count` | 1 |
| `support_trace_total` | 26 |
| `support_trace_included_count` | 13 |
| `support_trace_dropped_count` | 13 |
| `support_trace_hygiene_filtered_count` | 1 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 7 |
| `support_trace_semantic_mismatch_count` | 4 |
| `support_trace_duplicate_quote_count` | 0 |
| `support_trace_missing_verified_quote_count` | 1 |
| `final_support_specific_locator_count` | 10 |
| `final_support_weak_locator_count` | 3 |

## Negative & flaws

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `negative_evidence_candidate_count` | 6 |
| `negative_evidence_candidate_raw_count` | 6 |
| `review_negative_verified_count` | 0 |
| `reviewer_absence_verified_count` | 6 |
| `reviewer_absence_verified_claim_count` | 6 |
| `reviewer_absence_verified_flaw_count` | 6 |
| `total_review_negative_verified_count` | 6 |
| `quote_grounded_review_issue_count` | 0 |
| `obligation_grounded_review_issue_count` | 6 |
| `obligation_grounded_review_issue_claim_count` | 6 |
| `reviewer_candidate_review_issue_count` | 6 |
| `reviewer_candidate_review_issue_claim_count` | 6 |
| `reviewer_candidate_review_issue_critique_payload_count` | 4 |
| `reviewer_candidate_review_issue_deterministic_seed_count` | 2 |
| `reviewer_candidate_review_issue_other_candidate_count` | 0 |
| `claim_obligation_review_issue_count` | 0 |
| `claim_obligation_review_issue_claim_count` | 0 |
| `verified_review_issue_count` | 6 |
| `verified_review_issue_row_count` | 6 |
| `verified_review_issue_claim_count` | 6 |
| `review_issue_bundle_count` | 6 |
| `obligation_grounded_review_issue_cluster_count` | 5 |
| `reviewer_candidate_review_issue_cluster_count` | 5 |
| `claim_obligation_review_issue_cluster_count` | 0 |
| `verified_review_issue_cluster_count` | 5 |
| `duplicate_review_issue_row_count` | 1 |
| `verified_review_issue_cluster_recomputed_count` | 5 |
| `quote_grounded_review_issue_cluster_count` | 0 |
| `quote_grounded_direct_quote_duplicate_cluster_count` | 0 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 5 |
| `verified_review_issue_cluster_origin_critique_payload_count` | 3 |
| `verified_review_issue_cluster_origin_deterministic_seed_count` | 2 |
| `verified_review_issue_cluster_origin_claim_obligation_fallback_count` | 0 |
| `verified_review_issue_cluster_origin_direct_quote_count` | 0 |
| `verified_review_issue_cluster_origin_other_candidate_count` | 0 |
| `verified_review_issue_cluster_origin_other_count` | 0 |
| `verified_review_issue_cluster_source_reviewer_candidate_count` | 5 |
| `verified_review_issue_cluster_source_claim_obligation_count` | 0 |
| `verified_review_issue_cluster_source_direct_quote_count` | 0 |
| `verified_review_issue_cluster_slot_missing_baseline_count` | 2 |
| `verified_review_issue_cluster_slot_missing_ablation_count` | 3 |
| `verified_review_issue_cluster_slot_scope_or_robustness_count` | 0 |
| `verified_review_issue_cluster_slot_protocol_or_reproducibility_count` | 0 |
| `verified_review_issue_cluster_slot_efficiency_cost_count` | 0 |
| `verified_review_issue_cluster_slot_result_claim_mismatch_count` | 0 |
| `verified_review_issue_cluster_slot_direct_quote_count` | 0 |
| `verified_missing_ablation_cluster_count` | 3 |
| `verified_issue_without_recovery_count` | 1 |
| `verified_issue_cluster_without_recovery_count` | 1 |
| `review_issue_candidate_total` | 8 |
| `review_issue_candidate_verified` | 6 |
| `review_issue_candidate_retrieval_gap_rejected` | 0 |
| `review_issue_candidate_generic_item_rejected` | 0 |
| `review_issue_candidate_counterevidence_rejected` | 0 |
| `review_issue_candidate_missing_inventory_rejected` | 0 |
| `review_issue_candidate_off_claim_rejected` | 0 |
| `review_issue_candidate_review_worthiness_rejected` | 0 |
| `review_issue_candidate_missing_ablation_target_rejected` | 0 |
| `review_issue_candidate_missing_ablation_weak_action_rejected` | 0 |
| `review_issue_candidate_missing_ablation_generic_component_rejected` | 0 |
| `review_issue_candidate_missing_baseline_target_rejected` | 0 |
| `review_issue_candidate_missing_baseline_generic_target_rejected` | 0 |
| `review_issue_candidate_critique_payload_count` | 5 |
| `review_issue_candidate_deterministic_seed_count` | 3 |
| `critique_payload_gap_count` | 5 |
| `critique_payload_menu_bound_count` | 5 |
| `critique_payload_menu_candidate_count` | 5 |
| `critique_payload_bundle_built_count` | 4 |
| `critique_payload_verified_count` | 4 |
| `critique_payload_menu_bound_verified_count` | 4 |
| `critique_payload_verified_cluster_count` | 4 |
| `critique_direct_verified_cluster_count` | 4 |
| `critique_selected_verified_cluster_count` | 4 |
| `critique_selected_existing_seed_cluster_count` | 0 |
| `critique_selected_verified_by_existing_cluster_count` | 0 |
| `critique_selected_verified_cluster_detail_count` | 3 |
| `critique_only_candidate_count` | 0 |
| `critique_only_selected_menu_count` | 0 |
| `critique_only_verified_count` | 0 |
| `critique_only_verified_cluster_count` | 0 |
| `deterministic_seed_verified_cluster_count` | 1 |
| `candidate_menu_item_count` | 7 |
| `candidate_menu_item_used_count` | 5 |
| `candidate_menu_item_verified_count` | 4 |
| `candidate_menu_item_any_origin_verified_count` | 6 |
| `candidate_menu_item_verified_by_existing_cluster_count` | 0 |
| `candidate_menu_item_failed_count` | 1 |
| `candidate_menu_item_failed_detail_count` | 1 |
| `candidate_menu_item_failed_scope_menu_generic_target` | 0 |
| `candidate_menu_item_failed_efficiency_cost_menu_without_resource_anchor` | 0 |
| `candidate_menu_item_failed_missing_baseline_menu_generic_target` | 0 |
| `candidate_menu_item_failed_qualitative_vs_quantitative_result_gap_unsupported_type` | 0 |
| `candidate_menu_item_failed_reproducibility_menu_theory_context` | 0 |
| `candidate_menu_item_failed_full_text_baseline_or_comparison_counterevidence` | 0 |
| `candidate_menu_item_failed_full_text_protocol_or_result_counterevidence` | 0 |
| `candidate_menu_item_failed_missing_entity_already_observed_in_inventory` | 0 |
| `candidate_menu_item_failed_observed_inventory_irrelevant_to_issue_type` | 0 |
| `candidate_menu_item_failed_reviewer_candidate_expectation_not_auditable_in_paper` | 0 |
| `candidate_menu_item_failed_selected_menu_item_not_in_current_menu_or_filtered` | 0 |
| `candidate_menu_item_failed_not_verified_by_bundle` | 1 |
| `candidate_menu_item_failed_stage_menu_quality_guard` | 0 |
| `candidate_menu_item_failed_stage_concrete_item_check` | 0 |
| `candidate_menu_item_failed_stage_expectation_basis` | 0 |
| `candidate_menu_item_failed_stage_inventory_anchor` | 0 |
| `candidate_menu_item_failed_stage_inventory_relevance` | 0 |
| `candidate_menu_item_failed_stage_menu_lookup_or_quality_filter` | 0 |
| `candidate_menu_item_failed_stage_counterevidence` | 0 |
| `candidate_menu_item_failed_stage_review_worthiness` | 0 |
| `candidate_menu_item_failed_stage_bundle_verification` | 0 |
| `verified_missing_ablation_high_confidence` | 1 |
| `verified_missing_ablation_medium_confidence` | 3 |
| `review_issue_candidate_slot_missing_baseline` | 2 |
| `review_issue_candidate_slot_missing_ablation` | 5 |
| `review_issue_candidate_slot_scope_or_robustness` | 0 |
| `review_issue_candidate_slot_protocol_or_reproducibility` | 0 |
| `review_issue_candidate_slot_efficiency_cost` | 1 |
| `review_issue_candidate_slot_result_claim_mismatch` | 0 |
| `review_issue_verified_slot_missing_baseline` | 2 |
| `review_issue_verified_slot_missing_ablation` | 4 |
| `review_issue_verified_slot_scope_or_robustness` | 0 |
| `review_issue_verified_slot_protocol_or_reproducibility` | 0 |
| `review_issue_verified_slot_efficiency_cost` | 0 |
| `review_issue_verified_slot_result_claim_mismatch` | 0 |
| `review_issue_type_missing_ablation` | 4 |
| `review_issue_type_missing_baseline` | 2 |
| `review_issue_type_unfair_or_weak_baseline` | 0 |
| `review_issue_type_insufficient_evaluation` | 0 |
| `review_issue_type_missing_robustness_or_generalization` | 0 |
| `review_issue_type_evaluation_protocol_risk` | 0 |
| `review_issue_type_efficiency_cost_gap` | 0 |
| `review_issue_type_scope_overclaim` | 0 |
| `review_issue_type_result_claim_mismatch` | 0 |
| `review_issue_type_method_support_gap` | 0 |
| `review_issue_type_reproducibility_gap` | 0 |
| `review_issue_cluster_type_missing_ablation` | 3 |
| `review_issue_cluster_type_missing_baseline` | 2 |
| `review_issue_cluster_type_unfair_or_weak_baseline` | 0 |
| `review_issue_cluster_type_insufficient_evaluation` | 0 |
| `review_issue_cluster_type_missing_robustness_or_generalization` | 0 |
| `review_issue_cluster_type_evaluation_protocol_risk` | 0 |
| `review_issue_cluster_type_efficiency_cost_gap` | 0 |
| `review_issue_cluster_type_scope_overclaim` | 0 |
| `review_issue_cluster_type_result_claim_mismatch` | 0 |
| `review_issue_cluster_type_method_support_gap` | 0 |
| `review_issue_cluster_type_reproducibility_gap` | 0 |
| `paper_text_negative_candidate_count` | 2 |
| `author_limitation_only_count` | 0 |
| `prior_work_limitation_count` | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 |
| `positive_or_neutral_negative_rejected_count` | 0 |
| `positive_or_neutral_negative_unlinked_rejected_count` | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 |
| `semantic_negative_without_review_relation_count` | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 |
| `scope_limitation_as_verified_negative_count` | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 |
| `negative_evidence_linked_to_flaw_count` | 6 |
| `negative_evidence_linked_to_flaw_raw_count` | 6 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 7 |
| `verified_actionable_negative_flaw_count` | 7 |
| `verified_limitation_negative_flaw_count` | 0 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 5 |
| `negative_type_missing_baseline` | 2 |
| `negative_type_unfair_or_weak_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 |
| `negative_type_evaluation_protocol_risk` | 0 |
| `negative_type_efficiency_cost_gap` | 0 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_overclaim` | 0 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 0 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 7 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 3 |
| `negative_grounding_conflict_count` | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 |
| `negative_semantic_anchor_conflict_count` | 0 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 0 |
| `downgraded_flaw_count` | 1 |
| `potential_concern_count` | 7 |
| `diagnosis_pending_potential_concern_count` | 32 |
| `diagnosis_pending_potential_concern_claim_count` | 17 |
| `diagnosis_pending_concern_recorded_count` | 0 |
| `diagnosis_pending_concern_recorded_claim_count` | 0 |
| `coverage_gap_potential_concern_count` | 6 |
| `reviewer_inferred_potential_concern_count` | 6 |
| `final_potential_concern_total` | 12 |
| `diagnosis_pending_type_missing_ablation` | 3 |
| `diagnosis_pending_type_missing_baseline` | 5 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 8 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 0 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 2 |
| `diagnosis_pending_type_efficiency_cost_gap` | 2 |
| `diagnosis_pending_type_reproducibility_gap` | 5 |
| `diagnosis_pending_type_scope_overclaim` | 3 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 |
| `diagnosis_pending_type_method_support_gap` | 4 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `verified_coverage_gap_count` | 6 |
| `coverage_gap_potential_concern_count` | 6 |
| `reviewer_inferred_potential_concern_count` | 6 |
| `final_potential_concern_total` | 12 |
| `primary_claims_with_requirement_gaps` | 13 |

## State contamination

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `state_contamination_count` | 0 |
| `state_contamination_count_legacy` | 1 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 1 |
| `state_hygiene_warning_count` | 1 |
| `weak_target_warning_count` | 1 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 1 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 0 |
| `contamination_stale_gap_persistence` | 0 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 0 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `warning_zero_real_support` | 0 |
| `warning_stale_gap_persistence` | 1 |
| `warning_negative_evidence_overclaim` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 0 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `contested_support_total` | 13 |
| `contested_final_support_total` | 5 |
| `claims_with_contested_support` | 6 |
| `claims_with_contested_final_support` | 4 |
| `open_conflict_count` | 6 |
| `contested_relation_final_count` | 5 |
| `contested_relation_added_count` | 5 |
| `contested_relation_effective_count` | 5 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 0 |
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

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `evidence_gap_open_count` | 9 |
| `evidence_gap_resolved_count` | 12 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 0 |
| `state_hygiene_open_gap_count` | 6 |
| `state_hygiene_stale_gap_count` | 3 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 9 |
| `targeted_open_gap_count` | 9 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 20 |
| `unresolved_open_raw_count` | 37 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 34 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 10 |
| `programmatic_weak_locator_count` | 3 |
| `programmatic_locator_type_table_count` | 2 |
| `programmatic_locator_type_figure_count` | 2 |
| `programmatic_locator_type_section_count` | 5 |
| `programmatic_locator_type_algorithm_count` | 1 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 3 |
| `programmatic_high_confidence_locator_count` | 10 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `recovery_attempted` | 6 |
| `recovery_patch_validated` | 6 |
| `recovery_patch_committed` | 5 |
| `recovery_committed` | 5 |
| `recovery_success` | 5 |
| `hygiene_delta_improved` | 5 |
| `diagnosis_pending_recorded_layer` | 0 |
| `recovery_effective_repair` | 5 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_harmful_commit_committed` | 0 |
| `recovery_unsafe_downgrade_attempt_blocked` | 0 |
| `recovery_safe_resolution` | 6 |
| `recovery_safe_resolution_or_clean_state` | 5 |
| `hygiene_delta_or_safe_block` | 6 |
| `hygiene_delta_or_safe_block_or_clean_state` | 5 |
| `recovery_safe_blocked_weak_target` | 1 |
| `recovery_safe_blocked_terminal_target` | 0 |
| `recovery_terminal_turns` | 0 |
| `recovery_repeat_allowed_false_turns` | 0 |
| `recovery_target_gate_real_target_turns` | 5 |
| `recovery_target_gate_negative_verified_target_turns` | 0 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 0 |
| `recovery_target_gate_weak_target_turns` | 1 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 1 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 5 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Recovery case audit

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `recovery_case_rows` | 7 |
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
| `recovery_case_attempted_not_committed` | 2 |
| `recovery_case_committed_not_effective` | 0 |
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
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 0 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 |

## Hygiene

| metric | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 | interpreted safety outcome |
|---|---|---|
| `EVIDENCE_SEMANTIC_MISMATCH` | 1 | **safe_blocked_patch (semantic evidence validation mismatch)** |
| `SUCCESS` | 5 | **recovery_patch_committed** |

## Final decision distribution

| decision | P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123 |
|---|---|
| `reject` | 5 |
