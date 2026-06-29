# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260628_093956.jsonl` (label: P28_CANONICAL, papers: 20)
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
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 18 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 17 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 34 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 34 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 26 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 22 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 26 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | P28_CANONICAL |
|---|---|
| `evidence_agent_worker_turns` | 64 |
| `evidence_json_status_turns` | 56 |
| `evidence_json_valid_turns` | 56 |
| `evidence_json_partial_recovered_turns` | 0 |
| `evidence_json_fallback_turns` | 0 |
| `evidence_json_fallback_rate_pct` | 0 |
| `evidence_json_no_json_object_turns` | 0 |
| `evidence_json_invalid_json_turns` | 0 |
| `evidence_json_truncated_turns` | 0 |
| `evidence_json_prompt_chars_median` | 8590 |
| `evidence_json_raw_chars_median` | 891 |
| `quote_bank_nonzero_turns` | 64 |
| `payload_evidence_item_total` | 89 |
| `evidence_agent_nonempty_payload_turns` | 44 |
| `evidence_agent_question_only_turns` | 0 |
| `first_support_fallback_turns` | 1 |
| `model_adapter_quote_first_rewrite_count` | 0 |
| `model_adapter_strength_downgrade_count` | 0 |
| `small_model_quote_bank_augmentation_count` | 40 |
| `evidence_formation_dead_loop_count` | 0 |

## Positive support

| metric | P28_CANONICAL |
|---|---|
| `real_strong_support_total` | 34 |
| `independent_support_group_total` | 34 |
| `diagnostic_independent_support_group_total` | 45 |
| `claims_with_2plus_independent_or_diagnostic_support` | 14 |
| `empirical_real_strong_support_count` | 26 |
| `method_real_strong_support_count` | 8 |
| `table_or_figure_real_strong_support_count` | 13 |
| `result_or_experiment_real_strong_support_count` | 8 |
| `ablation_real_strong_support_count` | 5 |
| `abstract_real_strong_support_count` | 0 |
| `verified_moderate_support_total` | 11 |
| `moderate_diagnostic_support_total` | 11 |
| `moderate_absorbed_into_final_strong_count` | 15 |
| `moderate_remaining_diagnostic_count` | 11 |
| `diagnostic_support_signal_total` | 45 |
| `papers_with_real_strong_support` | 13 |
| `papers_with_empirical_support` | 11 |
| `papers_with_deep_support` | 11 |
| `positive_coverage_gap_papers` | 7 |
| `empirical_coverage_gap_papers` | 9 |
| `deep_support_gap_papers` | 9 |
| `claims_with_real_strong_support` | 29 |
| `claims_with_empirical_real_strong_support` | 22 |
| `claims_with_deep_support` | 22 |
| `claims_with_2plus_independent_support` | 5 |
| `primary_claim_total` | 60 |
| `primary_claims_with_real_strong_support` | 27 |
| `primary_claims_with_empirical_support` | 20 |
| `primary_claims_with_deep_support` | 20 |
| `zero_real_papers` | 7 |
| `final_support_total` | 34 |
| `final_support_direct_strong_count` | 19 |
| `final_support_promoted_from_medium_count` | 15 |
| `final_support_semantic_weak_promotion_count` | 0 |
| `near_miss_deep_moderate_support_count` | 1 |
| `near_miss_method_moderate_support_count` | 0 |
| `near_miss_specific_locator_moderate_count` | 0 |
| `near_miss_promoted_to_final_count` | 0 |
| `support_trace_total` | 81 |
| `support_trace_included_count` | 34 |
| `support_trace_dropped_count` | 47 |
| `support_trace_hygiene_filtered_count` | 16 |
| `support_trace_overridden_by_negative_burden_count` | 0 |
| `support_trace_weak_support_depth_count` | 14 |
| `support_trace_semantic_mismatch_count` | 13 |
| `support_trace_duplicate_quote_count` | 3 |
| `support_trace_missing_verified_quote_count` | 0 |
| `final_support_specific_locator_count` | 26 |
| `final_support_weak_locator_count` | 8 |

## Negative & flaws

| metric | P28_CANONICAL |
|---|---|
| `negative_evidence_candidate_count` | 22 |
| `negative_evidence_candidate_raw_count` | 22 |
| `review_negative_verified_count` | 0 |
| `reviewer_absence_verified_count` | 22 |
| `reviewer_absence_verified_claim_count` | 29 |
| `reviewer_absence_verified_flaw_count` | 22 |
| `total_review_negative_verified_count` | 22 |
| `quote_grounded_review_issue_count` | 0 |
| `obligation_grounded_review_issue_count` | 22 |
| `obligation_grounded_review_issue_claim_count` | 20 |
| `reviewer_candidate_review_issue_count` | 17 |
| `reviewer_candidate_review_issue_claim_count` | 16 |
| `claim_obligation_review_issue_count` | 5 |
| `claim_obligation_review_issue_claim_count` | 5 |
| `verified_review_issue_count` | 22 |
| `verified_review_issue_claim_count` | 20 |
| `review_issue_bundle_count` | 22 |
| `verified_issue_without_recovery_count` | 17 |
| `review_issue_candidate_total` | 64 |
| `review_issue_candidate_verified` | 17 |
| `review_issue_candidate_retrieval_gap_rejected` | 0 |
| `review_issue_candidate_generic_item_rejected` | 7 |
| `review_issue_candidate_counterevidence_rejected` | 34 |
| `review_issue_candidate_missing_inventory_rejected` | 18 |
| `review_issue_candidate_off_claim_rejected` | 0 |
| `review_issue_candidate_missing_ablation_target_rejected` | 3 |
| `review_issue_candidate_missing_ablation_weak_action_rejected` | 1 |
| `review_issue_candidate_missing_ablation_generic_component_rejected` | 0 |
| `verified_missing_ablation_high_confidence` | 7 |
| `verified_missing_ablation_medium_confidence` | 4 |
| `review_issue_type_missing_ablation` | 11 |
| `review_issue_type_missing_baseline` | 9 |
| `review_issue_type_unfair_or_weak_baseline` | 0 |
| `review_issue_type_insufficient_evaluation` | 0 |
| `review_issue_type_missing_robustness_or_generalization` | 0 |
| `review_issue_type_evaluation_protocol_risk` | 0 |
| `review_issue_type_efficiency_cost_gap` | 1 |
| `review_issue_type_scope_overclaim` | 1 |
| `review_issue_type_result_claim_mismatch` | 0 |
| `review_issue_type_method_support_gap` | 0 |
| `review_issue_type_reproducibility_gap` | 0 |
| `paper_text_negative_candidate_count` | 14 |
| `author_limitation_only_count` | 2 |
| `prior_work_limitation_count` | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 |
| `semantic_negative_without_review_relation_count` | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 3 |
| `scope_limitation_as_verified_negative_count` | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 |
| `negative_evidence_linked_to_flaw_count` | 22 |
| `negative_evidence_linked_to_flaw_raw_count` | 22 |
| `negative_evidence_unlinked_to_flaw` | 0 |
| `verified_negative_flaw_count` | 28 |
| `verified_actionable_negative_flaw_count` | 28 |
| `verified_limitation_negative_flaw_count` | 0 |
| `negative_type_direct_contradiction` | 0 |
| `negative_type_negative_result` | 0 |
| `negative_type_missing_ablation` | 16 |
| `negative_type_missing_baseline` | 13 |
| `negative_type_unfair_or_weak_baseline` | 0 |
| `negative_type_insufficient_evaluation` | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 |
| `negative_type_evaluation_protocol_risk` | 0 |
| `negative_type_efficiency_cost_gap` | 2 |
| `negative_type_reproducibility_gap` | 0 |
| `negative_type_scope_overclaim` | 2 |
| `negative_type_result_claim_mismatch` | 0 |
| `negative_type_scope_limitation` | 0 |
| `synced_actionable_negative_type_count` | 0 |
| `negative_type_neutral_control_context` | 0 |
| `negative_type_generic_gap` | 0 |
| `verified_potential_concern_count` | 28 |
| `grounded_weakness_count` | 0 |
| `assessment_limitation_flaw_count` | 17 |
| `negative_grounding_conflict_count` | 13 |
| `invalid_negative_evidence_id_count_legacy` | 13 |
| `negative_semantic_anchor_conflict_count` | 13 |
| `generic_gap_semantic_rejected_count` | 0 |
| `negative_evidence_semantic_rejected_count` | 3 |
| `downgraded_flaw_count` | 1 |
| `potential_concern_count` | 28 |
| `diagnosis_pending_potential_concern_count` | 123 |
| `diagnosis_pending_potential_concern_claim_count` | 61 |
| `diagnosis_pending_concern_recorded_count` | 0 |
| `diagnosis_pending_concern_recorded_claim_count` | 0 |
| `coverage_gap_potential_concern_count` | 30 |
| `reviewer_inferred_potential_concern_count` | 30 |
| `final_potential_concern_total` | 40 |
| `diagnosis_pending_type_missing_ablation` | 9 |
| `diagnosis_pending_type_missing_baseline` | 26 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 39 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 0 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 8 |
| `diagnosis_pending_type_efficiency_cost_gap` | 7 |
| `diagnosis_pending_type_reproducibility_gap` | 9 |
| `diagnosis_pending_type_scope_overclaim` | 6 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 |
| `diagnosis_pending_type_method_support_gap` | 19 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | P28_CANONICAL |
|---|---|
| `verified_coverage_gap_count` | 30 |
| `coverage_gap_potential_concern_count` | 30 |
| `reviewer_inferred_potential_concern_count` | 30 |
| `final_potential_concern_total` | 40 |
| `primary_claims_with_requirement_gaps` | 49 |

## State contamination

| metric | P28_CANONICAL |
|---|---|
| `state_contamination_count` | 30 |
| `state_contamination_count_legacy` | 30 |
| `harmful_state_contamination_count` | 0 |
| `repairable_state_warning_count` | 0 |
| `conservative_state_warning_count` | 30 |
| `state_hygiene_warning_count` | 30 |
| `weak_target_warning_count` | 30 |
| `repairable_contamination_target_count` | 0 |
| `conservative_contamination_target_count` | 30 |
| `blocked_fallback_contamination_target_count` | 0 |
| `blocked_empty_contamination_target_count` | 0 |
| `contamination_unsupported_with_strong_support` | 0 |
| `contamination_zero_real_support` | 7 |
| `contamination_stale_gap_persistence` | 10 |
| `contamination_unsupported_flaw_escalation` | 0 |
| `contamination_negative_evidence_overclaim` | 0 |
| `contamination_evidence_misbinding` | 13 |
| `contamination_meta_leakage` | 0 |
| `contamination_stale_flaw_persistence` | 0 |
| `contamination_harmful_recovery_risk` | 0 |
| `target_gate_real_target` | 0 |
| `target_gate_weak_target` | 30 |
| `target_gate_fallback_target` | 0 |
| `target_gate_empty_target` | 0 |

## Contested support

| metric | P28_CANONICAL |
|---|---|
| `contested_support_total` | 17 |
| `contested_final_support_total` | 5 |
| `claims_with_contested_support` | 7 |
| `claims_with_contested_final_support` | 4 |
| `open_conflict_count` | 31 |
| `contested_relation_final_count` | 11 |
| `contested_relation_added_count` | 12 |
| `contested_relation_effective_count` | 10 |
| `conflict_to_contested_resolution_count` | 0 |
| `negative_verified_target_preserved_count` | 7 |
| `diagnosis_pending_concern_commit_count` | 0 |
| `diagnosis_pending_concern_added_count` | 0 |
| `mark_contested_commit_count` | 12 |
| `mark_contested_with_positive_support_count` | 11 |
| `mark_contested_with_verified_negative_evidence_count` | 12 |
| `mark_contested_final_view_count` | 12 |
| `contested_relation_with_positive_support_count` | 10 |
| `contested_relation_with_verified_negative_evidence_count` | 11 |
| `contested_relation_final_view_count` | 11 |

## Gap cleanup & locator

| metric | P28_CANONICAL |
|---|---|
| `evidence_gap_open_count` | 34 |
| `evidence_gap_resolved_count` | 44 |
| `evidence_gap_superseded_count` | 0 |
| `evidence_gap_not_assessable_count` | 0 |
| `state_hygiene_open_gap_count` | 23 |
| `state_hygiene_stale_gap_count` | 11 |
| `targetless_open_gap_count` | 0 |
| `meta_or_context_open_gap_count` | 0 |
| `actionable_targeted_open_gap_count` | 0 |
| `diagnostic_targeted_open_gap_count` | 34 |
| `targeted_open_gap_count` | 34 |
| `assessment_limitation_open_gap_count` | 0 |
| `unresolved_open_count` | 63 |
| `unresolved_open_raw_count` | 175 |
| `unresolved_resolved_count` | 0 |
| `unresolved_deferred_count` | 173 |
| `targetless_unresolved_deferred_count` | 0 |
| `programmatic_specific_locator_count` | 26 |
| `programmatic_weak_locator_count` | 8 |
| `programmatic_locator_type_table_count` | 7 |
| `programmatic_locator_type_figure_count` | 8 |
| `programmatic_locator_type_section_count` | 11 |
| `programmatic_locator_type_algorithm_count` | 0 |
| `programmatic_locator_type_theorem_count` | 0 |
| `programmatic_locator_type_generic_count` | 8 |
| `programmatic_high_confidence_locator_count` | 26 |
| `programmatic_low_confidence_locator_count` | 0 |

## Recovery

| metric | P28_CANONICAL |
|---|---|
| `recovery_attempted` | 29 |
| `recovery_patch_validated` | 21 |
| `recovery_patch_committed` | 14 |
| `recovery_committed` | 14 |
| `recovery_success` | 14 |
| `hygiene_delta_improved` | 12 |
| `diagnosis_pending_recorded_layer` | 0 |
| `recovery_effective_repair` | 12 |
| `recovery_no_effect_commit` | 0 |
| `recovery_harmful_commit_risk` | 0 |
| `recovery_safe_resolution` | 25 |
| `recovery_safe_resolution_or_clean_state` | 18 |
| `hygiene_delta_or_safe_block` | 23 |
| `hygiene_delta_or_safe_block_or_clean_state` | 17 |
| `recovery_safe_blocked_weak_target` | 5 |
| `recovery_safe_blocked_terminal_target` | 6 |
| `recovery_terminal_turns` | 6 |
| `recovery_repeat_allowed_false_turns` | 6 |
| `recovery_target_gate_real_target_turns` | 14 |
| `recovery_target_gate_negative_verified_target_turns` | 7 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 0 |
| `recovery_target_gate_weak_target_turns` | 8 |
| `recovery_target_gate_fallback_target_turns` | 0 |
| `recovery_target_gate_empty_target_turns` | 0 |
| `recovery_patch_operation_reject_patch_turns` | 15 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 2 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 |
| `recovery_patch_operation_mark_contested_turns` | 12 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 0 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 |

## Recovery case audit

| metric | P28_CANONICAL |
|---|---|
| `recovery_case_rows` | 30 |
| `recovery_case_audit_error_count` | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 |
| `recovery_case_verified_review_negative_repair` | 0 |
| `recovery_case_verified_review_issue_repair` | 4 |
| `verified_issue_contested_repair` | 4 |
| `stale_absence_contested_repair` | 8 |
| `recovery_case_reviewer_inferred_negative_repair` | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 |
| `recovery_case_verified_review_issue_lifecycle_downgrade` | 0 |
| `recovery_case_reviewer_inferred_flaw_lifecycle_downgrade` | 0 |
| `recovery_case_state_hygiene_repair` | 0 |
| `recovery_case_assessment_limitation_routing` | 0 |
| `recovery_case_effective_repair_without_verified_negative` | 8 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 |
| `recovery_case_attempted_not_committed` | 16 |
| `recovery_case_committed_not_effective` | 2 |
| `recovery_case_effective_repair_turns` | 12 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 12 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 4 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 5 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 |
| `recovery_case_evidence_bucket_stale_reviewer_absence_audit` | 9 |
| `recovery_case_evidence_bucket_author_limitation_only` | 3 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 5 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 |
| `recovery_case_evidence_bucket_support_only` | 2 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 |

## Hygiene

| metric | P28_CANONICAL |
|---|---|
| `final_nonreal_strong_support` | 0 |
| `low_score_promoted_strong` | 0 |
| `final_report_leakage_paper_count` | 0 |
| `user_report_leakage_paper_count` | 0 |
| `synthetic_marker_in_supporting_count` | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 |

## Recovery failure codes

| code | P28_CANONICAL | interpreted safety outcome |
|---|---|---|
| `ACTIONABLE_CONCERN_PRESERVED` | 1 | **safe_terminal_block (verified potential concern preserved)** |
| `BLOCKED_BY_POLICY` | 7 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_SEMANTIC_MISMATCH` | 2 | **safe_blocked_patch (semantic evidence validation mismatch)** |
| `EVIDENCE_TARGET_MISMATCH` | 2 | **safe_blocked_patch (missing or unverified IDs)** |
| `INSUFFICIENT_EVIDENCE` | 1 | **safe_blocked_patch (insufficient evidence criteria)** |
| `NO_EFFECT_PATCH` | 1 | **safe_blocked_patch (no state change needed)** |
| `SEMANTIC_MISMATCH` | 1 | **safe_blocked_patch (semantic validation mismatch)** |
| `SUCCESS` | 14 | **recovery_patch_committed** |

## Final decision distribution

| decision | P28_CANONICAL |
|---|---|
| `reject` | 20 |

