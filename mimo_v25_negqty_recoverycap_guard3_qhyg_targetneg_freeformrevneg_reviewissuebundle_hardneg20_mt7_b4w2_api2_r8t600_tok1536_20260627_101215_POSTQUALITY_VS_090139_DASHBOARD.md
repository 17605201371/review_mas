# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215.jsonl` (label: BOLDISSUE_101215_POSTQUALITY, papers: 20)
- baseline:  `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_090139.jsonl` (label: PREV_090139, papers: 20)
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
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 19 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 19 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 73 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 72 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 52 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 43 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 50 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 79 | 71 | -8 |
| `evidence_json_status_turns` | 79 | 67 | -12 |
| `evidence_json_valid_turns` | 79 | 67 | -12 |
| `evidence_json_partial_recovered_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_rate_pct` | 0 | 0 | 0 |
| `evidence_json_no_json_object_turns` | 0 | 0 | 0 |
| `evidence_json_invalid_json_turns` | 0 | 0 | 0 |
| `evidence_json_truncated_turns` | 0 | 0 | 0 |
| `evidence_json_prompt_chars_median` | 7826 | 7826 | 0 |
| `evidence_json_raw_chars_median` | 1360 | 2419 | +1059 |
| `quote_bank_nonzero_turns` | 79 | 70 | -9 |
| `payload_evidence_item_total` | 147 | 138 | -9 |
| `evidence_agent_nonempty_payload_turns` | 66 | 53 | -13 |
| `evidence_agent_question_only_turns` | 2 | 0 | -2 |
| `first_support_fallback_turns` | 1 | 2 | +1 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 52 | 43 | -9 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `real_strong_support_total` | 66 | 73 | +7 |
| `independent_support_group_total` | 65 | 72 | +7 |
| `diagnostic_independent_support_group_total` | 97 | 98 | +1 |
| `claims_with_2plus_independent_or_diagnostic_support` | 34 | 34 | 0 |
| `empirical_real_strong_support_count` | 53 | 52 | -1 |
| `method_real_strong_support_count` | 13 | 21 | +8 |
| `table_or_figure_real_strong_support_count` | 40 | 31 | -9 |
| `result_or_experiment_real_strong_support_count` | 11 | 18 | +7 |
| `ablation_real_strong_support_count` | 2 | 3 | +1 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 35 | 26 | -9 |
| `moderate_diagnostic_support_total` | 35 | 26 | -9 |
| `moderate_absorbed_into_final_strong_count` | 31 | 43 | +12 |
| `moderate_remaining_diagnostic_count` | 35 | 26 | -9 |
| `diagnostic_support_signal_total` | 101 | 99 | -2 |
| `papers_with_real_strong_support` | 18 | 19 | +1 |
| `papers_with_empirical_support` | 18 | 19 | +1 |
| `papers_with_deep_support` | 18 | 19 | +1 |
| `positive_coverage_gap_papers` | 2 | 1 | -1 |
| `empirical_coverage_gap_papers` | 2 | 1 | -1 |
| `deep_support_gap_papers` | 2 | 1 | -1 |
| `claims_with_real_strong_support` | 46 | 46 | 0 |
| `claims_with_empirical_real_strong_support` | 39 | 39 | 0 |
| `claims_with_deep_support` | 40 | 43 | +3 |
| `claims_with_2plus_independent_support` | 17 | 25 | +8 |
| `primary_claim_total` | 57 | 60 | +3 |
| `primary_claims_with_real_strong_support` | 42 | 43 | +1 |
| `primary_claims_with_empirical_support` | 36 | 36 | 0 |
| `primary_claims_with_deep_support` | 37 | 40 | +3 |
| `zero_real_papers` | 2 | 1 | -1 |
| `final_support_total` | 66 | 73 | +7 |
| `final_support_direct_strong_count` | 35 | 30 | -5 |
| `final_support_promoted_from_medium_count` | 31 | 43 | +12 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 3 | +3 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 0 | 1 | +1 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 156 | 157 | +1 |
| `support_trace_included_count` | 66 | 73 | +7 |
| `support_trace_dropped_count` | 90 | 84 | -6 |
| `support_trace_hygiene_filtered_count` | 37 | 37 | 0 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 20 | 25 | +5 |
| `support_trace_semantic_mismatch_count` | 21 | 19 | -2 |
| `support_trace_duplicate_quote_count` | 8 | 3 | -5 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 48 | 50 | +2 |
| `final_support_weak_locator_count` | 18 | 23 | +5 |

## Negative & flaws

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 6 | 3 | -3 |
| `negative_evidence_candidate_raw_count` | 6 | 3 | -3 |
| `review_negative_verified_count` | 0 | 0 | 0 |
| `reviewer_absence_verified_count` | 6 | 3 | -3 |
| `reviewer_absence_verified_claim_count` | 5 | 5 | 0 |
| `reviewer_absence_verified_flaw_count` | 5 | 3 | -2 |
| `total_review_negative_verified_count` | 6 | 3 | -3 |
| `quote_grounded_review_issue_count` | 0 | 0 | 0 |
| `obligation_grounded_review_issue_count` | 6 | 3 | -3 |
| `obligation_grounded_review_issue_claim_count` | 5 | 3 | -2 |
| `verified_review_issue_count` | 6 | 3 | -3 |
| `verified_review_issue_claim_count` | 5 | 3 | -2 |
| `review_issue_bundle_count` | 6 | 3 | -3 |
| `review_issue_type_missing_ablation` | 2 | 1 | -1 |
| `review_issue_type_missing_baseline` | 1 | 0 | -1 |
| `review_issue_type_unfair_or_weak_baseline` | 1 | 0 | -1 |
| `review_issue_type_insufficient_evaluation` | 0 | 0 | 0 |
| `review_issue_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `review_issue_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `review_issue_type_efficiency_cost_gap` | 1 | 1 | 0 |
| `review_issue_type_scope_overclaim` | 0 | 0 | 0 |
| `review_issue_type_result_claim_mismatch` | 0 | 0 | 0 |
| `review_issue_type_method_support_gap` | 0 | 1 | +1 |
| `review_issue_type_reproducibility_gap` | 1 | 0 | -1 |
| `paper_text_negative_candidate_count` | 21 | 8 | -13 |
| `author_limitation_only_count` | 3 | 0 | -3 |
| `prior_work_limitation_count` | 0 | 0 | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 | 0 | 0 |
| `semantic_negative_without_review_relation_count` | 0 | 0 | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 5 | 1 | -4 |
| `scope_limitation_as_verified_negative_count` | 0 | 0 | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 6 | 3 | -3 |
| `negative_evidence_linked_to_flaw_raw_count` | 6 | 3 | -3 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 5 | 4 | -1 |
| `verified_actionable_negative_flaw_count` | 5 | 4 | -1 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 0 | 0 | 0 |
| `negative_type_missing_ablation` | 3 | 1 | -2 |
| `negative_type_missing_baseline` | 1 | 0 | -1 |
| `negative_type_unfair_or_weak_baseline` | 1 | 0 | -1 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `negative_type_evaluation_protocol_risk` | 0 | 0 | 0 |
| `negative_type_efficiency_cost_gap` | 0 | 1 | +1 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 0 | 0 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 5 | 4 | -1 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 16 | 13 | -3 |
| `negative_grounding_conflict_count` | 4 | 6 | +2 |
| `invalid_negative_evidence_id_count_legacy` | 4 | 6 | +2 |
| `negative_semantic_anchor_conflict_count` | 4 | 6 | +2 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 1 | 2 | +1 |
| `downgraded_flaw_count` | 1 | 3 | +2 |
| `potential_concern_count` | 5 | 4 | -1 |
| `diagnosis_pending_potential_concern_count` | 85 | 91 | +6 |
| `diagnosis_pending_potential_concern_claim_count` | 48 | 53 | +5 |
| `diagnosis_pending_concern_recorded_count` | 1 | 5 | +4 |
| `diagnosis_pending_concern_recorded_claim_count` | 1 | 5 | +4 |
| `coverage_gap_potential_concern_count` | 16 | 23 | +7 |
| `reviewer_inferred_potential_concern_count` | 16 | 23 | +7 |
| `final_potential_concern_total` | 19 | 25 | +6 |
| `diagnosis_pending_type_missing_ablation` | 4 | 8 | +4 |
| `diagnosis_pending_type_missing_baseline` | 18 | 23 | +5 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 18 | 21 | +3 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 0 | 1 | +1 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 8 | 5 | -3 |
| `diagnosis_pending_type_efficiency_cost_gap` | 7 | 5 | -2 |
| `diagnosis_pending_type_reproducibility_gap` | 13 | 7 | -6 |
| `diagnosis_pending_type_scope_overclaim` | 4 | 7 | +3 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 | 0 | 0 |
| `diagnosis_pending_type_method_support_gap` | 13 | 14 | +1 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `verified_coverage_gap_count` | 16 | 23 | +7 |
| `coverage_gap_potential_concern_count` | 16 | 23 | +7 |
| `reviewer_inferred_potential_concern_count` | 16 | 23 | +7 |
| `final_potential_concern_total` | 19 | 25 | +6 |
| `primary_claims_with_requirement_gaps` | 33 | 43 | +10 |

## State contamination

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `state_contamination_count` | 8 | 9 | +1 |
| `state_contamination_count_legacy` | 8 | 9 | +1 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 8 | 9 | +1 |
| `state_hygiene_warning_count` | 8 | 9 | +1 |
| `weak_target_warning_count` | 8 | 9 | +1 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 8 | 9 | +1 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 2 | 1 | -1 |
| `contamination_stale_gap_persistence` | 1 | 2 | +1 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 4 | 6 | +2 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 1 | 0 | -1 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 8 | 9 | +1 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `contested_support_total` | 5 | 2 | -3 |
| `contested_final_support_total` | 2 | 2 | 0 |
| `claims_with_contested_support` | 3 | 1 | -2 |
| `claims_with_contested_final_support` | 2 | 1 | -1 |
| `open_conflict_count` | 27 | 27 | 0 |
| `contested_relation_final_count` | 0 | 3 | +3 |
| `contested_relation_added_count` | 0 | 3 | +3 |
| `contested_relation_effective_count` | 0 | 3 | +3 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 2 | 1 | -1 |
| `diagnosis_pending_concern_commit_count` | 1 | 5 | +4 |
| `diagnosis_pending_concern_added_count` | 1 | 5 | +4 |
| `mark_contested_commit_count` | 0 | 3 | +3 |
| `mark_contested_with_positive_support_count` | 0 | 3 | +3 |
| `mark_contested_with_verified_negative_evidence_count` | 0 | 3 | +3 |
| `mark_contested_final_view_count` | 0 | 3 | +3 |
| `contested_relation_with_positive_support_count` | 0 | 3 | +3 |
| `contested_relation_with_verified_negative_evidence_count` | 0 | 3 | +3 |
| `contested_relation_final_view_count` | 0 | 3 | +3 |

## Gap cleanup & locator

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 15 | 21 | +6 |
| `evidence_gap_resolved_count` | 67 | 51 | -16 |
| `evidence_gap_superseded_count` | 0 | 1 | +1 |
| `evidence_gap_not_assessable_count` | 5 | 2 | -3 |
| `state_hygiene_open_gap_count` | 13 | 18 | +5 |
| `state_hygiene_stale_gap_count` | 2 | 3 | +1 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 1 | 0 | -1 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 14 | 21 | +7 |
| `targeted_open_gap_count` | 14 | 21 | +7 |
| `assessment_limitation_open_gap_count` | 1 | 0 | -1 |
| `unresolved_open_count` | 53 | 55 | +2 |
| `unresolved_open_raw_count` | 148 | 137 | -11 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 143 | 135 | -8 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 48 | 50 | +2 |
| `programmatic_weak_locator_count` | 18 | 23 | +5 |
| `programmatic_locator_type_table_count` | 20 | 14 | -6 |
| `programmatic_locator_type_figure_count` | 13 | 18 | +5 |
| `programmatic_locator_type_section_count` | 13 | 16 | +3 |
| `programmatic_locator_type_algorithm_count` | 2 | 1 | -1 |
| `programmatic_locator_type_theorem_count` | 0 | 1 | +1 |
| `programmatic_locator_type_generic_count` | 18 | 23 | +5 |
| `programmatic_high_confidence_locator_count` | 48 | 50 | +2 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `recovery_attempted` | 12 | 13 | +1 |
| `recovery_patch_validated` | 5 | 9 | +4 |
| `recovery_patch_committed` | 4 | 8 | +4 |
| `recovery_committed` | 4 | 8 | +4 |
| `recovery_success` | 4 | 8 | +4 |
| `hygiene_delta_improved` | 0 | 3 | +3 |
| `diagnosis_pending_recorded_layer` | 1 | 5 | +4 |
| `recovery_effective_repair` | 0 | 3 | +3 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 1 | 0 | -1 |
| `recovery_safe_resolution` | 10 | 11 | +1 |
| `recovery_safe_resolution_or_clean_state` | 17 | 19 | +2 |
| `hygiene_delta_or_safe_block` | 6 | 6 | 0 |
| `hygiene_delta_or_safe_block_or_clean_state` | 14 | 19 | +5 |
| `recovery_safe_blocked_weak_target` | 4 | 2 | -2 |
| `recovery_safe_blocked_terminal_target` | 2 | 1 | -1 |
| `recovery_terminal_turns` | 3 | 1 | -2 |
| `recovery_repeat_allowed_false_turns` | 3 | 1 | -2 |
| `recovery_target_gate_real_target_turns` | 4 | 3 | -1 |
| `recovery_target_gate_negative_verified_target_turns` | 2 | 1 | -1 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 1 | 5 | +4 |
| `recovery_target_gate_weak_target_turns` | 4 | 2 | -2 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 1 | 2 | +1 |
| `recovery_patch_operation_reject_patch_turns` | 8 | 5 | -3 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 3 | 0 | -3 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 0 | 3 | +3 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 1 | 5 | +4 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Recovery case audit

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `recovery_case_rows` | 12 | 14 | +2 |
| `recovery_case_audit_error_count` | 0 | 0 | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 | 0 | 0 |
| `recovery_case_verified_review_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_review_issue_repair` | 0 | 1 | +1 |
| `recovery_case_reviewer_inferred_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_verified_review_issue_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_reviewer_inferred_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_state_hygiene_repair` | 0 | 0 | 0 |
| `recovery_case_assessment_limitation_routing` | 0 | 0 | 0 |
| `recovery_case_effective_repair_without_verified_negative` | 0 | 2 | +2 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_attempted_not_committed` | 8 | 6 | -2 |
| `recovery_case_committed_not_effective` | 4 | 5 | +1 |
| `recovery_case_effective_repair_turns` | 0 | 3 | +3 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 0 | 3 | +3 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 | 0 | 0 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 2 | 1 | -1 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 2 | 1 | -1 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 2 | 0 | -2 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 | 0 | 0 |

## Hygiene

| metric | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | PREV_090139 | BOLDISSUE_101215_POSTQUALITY | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 7 | 4 | -3 | **safe_blocked_patch (policy restriction/abstention)** |
| `SEMANTIC_MISMATCH` | 1 | 1 | 0 | **safe_blocked_patch (semantic validation mismatch)** |
| `SUCCESS` | 4 | 8 | +4 | **recovery_patch_committed** |

## Final decision distribution

| decision | PREV_090139 | BOLDISSUE_101215_POSTQUALITY |
|---|---|---|
| `reject` | 20 | 20 |
