# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.jsonl` (label: CANDPRIORITY1_RECOMPUTE, papers: 20)
- baseline:  `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215.jsonl` (label: STRUCTEXPECT2_101215, papers: 20)
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
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 17 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 71 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 70 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 58 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 37 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 48 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 71 | 82 | +11 |
| `evidence_json_status_turns` | 67 | 79 | +12 |
| `evidence_json_valid_turns` | 67 | 79 | +12 |
| `evidence_json_partial_recovered_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_rate_pct` | 0 | 0 | 0 |
| `evidence_json_no_json_object_turns` | 0 | 0 | 0 |
| `evidence_json_invalid_json_turns` | 0 | 0 | 0 |
| `evidence_json_truncated_turns` | 0 | 0 | 0 |
| `evidence_json_prompt_chars_median` | 7826 | 7826 | 0 |
| `evidence_json_raw_chars_median` | 2419 | 1436 | -983 |
| `quote_bank_nonzero_turns` | 70 | 82 | +12 |
| `payload_evidence_item_total` | 138 | 135 | -3 |
| `evidence_agent_nonempty_payload_turns` | 53 | 64 | +11 |
| `evidence_agent_question_only_turns` | 0 | 3 | +3 |
| `first_support_fallback_turns` | 2 | 0 | -2 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 43 | 44 | +1 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `real_strong_support_total` | 73 | 71 | -2 |
| `independent_support_group_total` | 72 | 70 | -2 |
| `diagnostic_independent_support_group_total` | 98 | 86 | -12 |
| `claims_with_2plus_independent_or_diagnostic_support` | 34 | 31 | -3 |
| `empirical_real_strong_support_count` | 52 | 58 | +6 |
| `method_real_strong_support_count` | 21 | 13 | -8 |
| `table_or_figure_real_strong_support_count` | 31 | 32 | +1 |
| `result_or_experiment_real_strong_support_count` | 18 | 21 | +3 |
| `ablation_real_strong_support_count` | 3 | 5 | +2 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 26 | 20 | -6 |
| `moderate_diagnostic_support_total` | 26 | 20 | -6 |
| `moderate_absorbed_into_final_strong_count` | 43 | 32 | -11 |
| `moderate_remaining_diagnostic_count` | 26 | 20 | -6 |
| `diagnostic_support_signal_total` | 99 | 91 | -8 |
| `papers_with_real_strong_support` | 19 | 18 | -1 |
| `papers_with_empirical_support` | 19 | 18 | -1 |
| `papers_with_deep_support` | 19 | 18 | -1 |
| `positive_coverage_gap_papers` | 1 | 2 | +1 |
| `empirical_coverage_gap_papers` | 1 | 2 | +1 |
| `deep_support_gap_papers` | 1 | 2 | +1 |
| `claims_with_real_strong_support` | 46 | 40 | -6 |
| `claims_with_empirical_real_strong_support` | 39 | 35 | -4 |
| `claims_with_deep_support` | 43 | 37 | -6 |
| `claims_with_2plus_independent_support` | 25 | 22 | -3 |
| `primary_claim_total` | 60 | 59 | -1 |
| `primary_claims_with_real_strong_support` | 43 | 37 | -6 |
| `primary_claims_with_empirical_support` | 36 | 33 | -3 |
| `primary_claims_with_deep_support` | 40 | 35 | -5 |
| `zero_real_papers` | 1 | 2 | +1 |
| `final_support_total` | 73 | 71 | -2 |
| `final_support_direct_strong_count` | 30 | 39 | +9 |
| `final_support_promoted_from_medium_count` | 43 | 32 | -11 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 3 | 1 | -2 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 1 | 1 | 0 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 157 | 148 | -9 |
| `support_trace_included_count` | 73 | 71 | -2 |
| `support_trace_dropped_count` | 84 | 77 | -7 |
| `support_trace_hygiene_filtered_count` | 37 | 19 | -18 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 25 | 27 | +2 |
| `support_trace_semantic_mismatch_count` | 19 | 22 | +3 |
| `support_trace_duplicate_quote_count` | 3 | 7 | +4 |
| `support_trace_missing_verified_quote_count` | 0 | 1 | +1 |
| `final_support_specific_locator_count` | 50 | 48 | -2 |
| `final_support_weak_locator_count` | 23 | 23 | 0 |

## Negative & flaws

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 8 | 8 | 0 |
| `negative_evidence_candidate_raw_count` | 9 | 9 | 0 |
| `review_negative_verified_count` | 0 | 1 | +1 |
| `reviewer_absence_verified_count` | 8 | 7 | -1 |
| `reviewer_absence_verified_claim_count` | 8 | 10 | +2 |
| `reviewer_absence_verified_flaw_count` | 8 | 7 | -1 |
| `total_review_negative_verified_count` | 8 | 8 | 0 |
| `quote_grounded_review_issue_count` | 0 | 1 | +1 |
| `obligation_grounded_review_issue_count` | 8 | 7 | -1 |
| `obligation_grounded_review_issue_claim_count` | 8 | 7 | -1 |
| `reviewer_candidate_review_issue_count` | 5 | 3 | -2 |
| `reviewer_candidate_review_issue_claim_count` | 5 | 3 | -2 |
| `claim_obligation_review_issue_count` | 3 | 4 | +1 |
| `claim_obligation_review_issue_claim_count` | 3 | 4 | +1 |
| `verified_review_issue_count` | 8 | 8 | 0 |
| `verified_review_issue_claim_count` | 8 | 8 | 0 |
| `review_issue_bundle_count` | 8 | 7 | -1 |
| `review_issue_type_missing_ablation` | 2 | 1 | -1 |
| `review_issue_type_missing_baseline` | 1 | 0 | -1 |
| `review_issue_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `review_issue_type_insufficient_evaluation` | 3 | 1 | -2 |
| `review_issue_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `review_issue_type_evaluation_protocol_risk` | 0 | 1 | +1 |
| `review_issue_type_efficiency_cost_gap` | 1 | 2 | +1 |
| `review_issue_type_scope_overclaim` | 0 | 0 | 0 |
| `review_issue_type_result_claim_mismatch` | 0 | 0 | 0 |
| `review_issue_type_method_support_gap` | 1 | 1 | 0 |
| `review_issue_type_reproducibility_gap` | 0 | 1 | +1 |
| `paper_text_negative_candidate_count` | 8 | 22 | +14 |
| `author_limitation_only_count` | 0 | 2 | +2 |
| `prior_work_limitation_count` | 0 | 0 | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 | 0 | 0 |
| `semantic_negative_without_review_relation_count` | 0 | 0 | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 | 1 | 0 |
| `scope_limitation_as_verified_negative_count` | 0 | 0 | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 8 | 8 | 0 |
| `negative_evidence_linked_to_flaw_raw_count` | 9 | 9 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 10 | 10 | 0 |
| `verified_actionable_negative_flaw_count` | 10 | 10 | 0 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 0 | 1 | +1 |
| `negative_type_missing_ablation` | 2 | 1 | -1 |
| `negative_type_missing_baseline` | 2 | 0 | -2 |
| `negative_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 3 | 2 | -1 |
| `negative_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `negative_type_evaluation_protocol_risk` | 0 | 1 | +1 |
| `negative_type_efficiency_cost_gap` | 1 | 3 | +2 |
| `negative_type_reproducibility_gap` | 0 | 1 | +1 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 0 | 0 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 10 | 10 | 0 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 10 | 27 | +17 |
| `negative_grounding_conflict_count` | 3 | 13 | +10 |
| `invalid_negative_evidence_id_count_legacy` | 3 | 13 | +10 |
| `negative_semantic_anchor_conflict_count` | 3 | 13 | +10 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 2 | 1 | -1 |
| `downgraded_flaw_count` | 2 | 4 | +2 |
| `potential_concern_count` | 10 | 10 | 0 |
| `diagnosis_pending_potential_concern_count` | 91 | 99 | +8 |
| `diagnosis_pending_potential_concern_claim_count` | 53 | 53 | 0 |
| `diagnosis_pending_concern_recorded_count` | 5 | 2 | -3 |
| `diagnosis_pending_concern_recorded_claim_count` | 5 | 2 | -3 |
| `coverage_gap_potential_concern_count` | 23 | 25 | +2 |
| `reviewer_inferred_potential_concern_count` | 23 | 25 | +2 |
| `final_potential_concern_total` | 28 | 27 | -1 |
| `diagnosis_pending_type_missing_ablation` | 8 | 10 | +2 |
| `diagnosis_pending_type_missing_baseline` | 23 | 19 | -4 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 21 | 21 | 0 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 1 | 6 | +5 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 5 | 10 | +5 |
| `diagnosis_pending_type_efficiency_cost_gap` | 5 | 4 | -1 |
| `diagnosis_pending_type_reproducibility_gap` | 7 | 7 | 0 |
| `diagnosis_pending_type_scope_overclaim` | 7 | 8 | +1 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 | 0 | 0 |
| `diagnosis_pending_type_method_support_gap` | 14 | 14 | 0 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `verified_coverage_gap_count` | 23 | 25 | +2 |
| `coverage_gap_potential_concern_count` | 23 | 25 | +2 |
| `reviewer_inferred_potential_concern_count` | 23 | 25 | +2 |
| `final_potential_concern_total` | 28 | 27 | -1 |
| `primary_claims_with_requirement_gaps` | 43 | 44 | +1 |

## State contamination

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `state_contamination_count` | 10 | 16 | +6 |
| `state_contamination_count_legacy` | 10 | 16 | +6 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 10 | 16 | +6 |
| `state_hygiene_warning_count` | 10 | 16 | +6 |
| `weak_target_warning_count` | 10 | 16 | +6 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 10 | 16 | +6 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 1 | 2 | +1 |
| `contamination_stale_gap_persistence` | 6 | 1 | -5 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 3 | 13 | +10 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 10 | 16 | +6 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `contested_support_total` | 6 | 19 | +13 |
| `contested_final_support_total` | 4 | 9 | +5 |
| `claims_with_contested_support` | 2 | 6 | +4 |
| `claims_with_contested_final_support` | 2 | 6 | +4 |
| `open_conflict_count` | 27 | 34 | +7 |
| `contested_relation_final_count` | 3 | 9 | +6 |
| `contested_relation_added_count` | 3 | 10 | +7 |
| `contested_relation_effective_count` | 3 | 9 | +6 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 1 | 2 | +1 |
| `diagnosis_pending_concern_commit_count` | 5 | 2 | -3 |
| `diagnosis_pending_concern_added_count` | 5 | 2 | -3 |
| `mark_contested_commit_count` | 3 | 10 | +7 |
| `mark_contested_with_positive_support_count` | 3 | 10 | +7 |
| `mark_contested_with_verified_negative_evidence_count` | 3 | 10 | +7 |
| `mark_contested_final_view_count` | 3 | 10 | +7 |
| `contested_relation_with_positive_support_count` | 3 | 9 | +6 |
| `contested_relation_with_verified_negative_evidence_count` | 3 | 9 | +6 |
| `contested_relation_final_view_count` | 3 | 9 | +6 |

## Gap cleanup & locator

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 21 | 17 | -4 |
| `evidence_gap_resolved_count` | 51 | 56 | +5 |
| `evidence_gap_superseded_count` | 1 | 0 | -1 |
| `evidence_gap_not_assessable_count` | 2 | 2 | 0 |
| `state_hygiene_open_gap_count` | 14 | 13 | -1 |
| `state_hygiene_stale_gap_count` | 7 | 4 | -3 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 21 | 17 | -4 |
| `targeted_open_gap_count` | 21 | 17 | -4 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 55 | 58 | +3 |
| `unresolved_open_raw_count` | 137 | 159 | +22 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 135 | 154 | +19 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 50 | 48 | -2 |
| `programmatic_weak_locator_count` | 23 | 23 | 0 |
| `programmatic_locator_type_table_count` | 14 | 17 | +3 |
| `programmatic_locator_type_figure_count` | 18 | 11 | -7 |
| `programmatic_locator_type_section_count` | 16 | 19 | +3 |
| `programmatic_locator_type_algorithm_count` | 1 | 1 | 0 |
| `programmatic_locator_type_theorem_count` | 1 | 0 | -1 |
| `programmatic_locator_type_generic_count` | 23 | 23 | 0 |
| `programmatic_high_confidence_locator_count` | 50 | 46 | -4 |
| `programmatic_low_confidence_locator_count` | 0 | 2 | +2 |

## Recovery

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `recovery_attempted` | 13 | 17 | +4 |
| `recovery_patch_validated` | 9 | 16 | +7 |
| `recovery_patch_committed` | 8 | 16 | +8 |
| `recovery_committed` | 8 | 16 | +8 |
| `recovery_success` | 8 | 16 | +8 |
| `hygiene_delta_improved` | 3 | 11 | +8 |
| `diagnosis_pending_recorded_layer` | 5 | 2 | -3 |
| `recovery_effective_repair` | 3 | 11 | +8 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 11 | 17 | +6 |
| `recovery_safe_resolution_or_clean_state` | 19 | 19 | 0 |
| `hygiene_delta_or_safe_block` | 6 | 12 | +6 |
| `hygiene_delta_or_safe_block_or_clean_state` | 19 | 17 | -2 |
| `recovery_safe_blocked_weak_target` | 2 | 0 | -2 |
| `recovery_safe_blocked_terminal_target` | 1 | 1 | 0 |
| `recovery_terminal_turns` | 1 | 1 | 0 |
| `recovery_repeat_allowed_false_turns` | 1 | 1 | 0 |
| `recovery_target_gate_real_target_turns` | 3 | 13 | +10 |
| `recovery_target_gate_negative_verified_target_turns` | 1 | 2 | +1 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 5 | 2 | -3 |
| `recovery_target_gate_weak_target_turns` | 2 | 0 | -2 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 2 | 0 | -2 |
| `recovery_patch_operation_reject_patch_turns` | 5 | 1 | -4 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 | 3 | +3 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 | 1 | +1 |
| `recovery_patch_operation_mark_contested_turns` | 3 | 10 | +7 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 5 | 2 | -3 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Recovery case audit

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `recovery_case_rows` | 14 | 18 | +4 |
| `recovery_case_audit_error_count` | 0 | 0 | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 | 0 | 0 |
| `recovery_case_verified_review_negative_repair` | 0 | 1 | +1 |
| `recovery_case_verified_review_issue_repair` | 2 | 5 | +3 |
| `recovery_case_reviewer_inferred_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_verified_review_issue_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_reviewer_inferred_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_state_hygiene_repair` | 0 | 0 | 0 |
| `recovery_case_assessment_limitation_routing` | 0 | 1 | +1 |
| `recovery_case_effective_repair_without_verified_negative` | 1 | 4 | +3 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_attempted_not_committed` | 6 | 2 | -4 |
| `recovery_case_committed_not_effective` | 5 | 5 | 0 |
| `recovery_case_effective_repair_turns` | 3 | 11 | +8 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 3 | 10 | +7 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 0 | 1 | +1 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 2 | 6 | +4 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 0 | 1 | +1 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 2 | 6 | +4 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 0 | 3 | +3 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 | 0 | 0 |

## Hygiene

| metric | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 4 | 1 | -3 | **safe_blocked_patch (policy restriction/abstention)** |
| `SEMANTIC_MISMATCH` | 1 | 0 | -1 | **safe_blocked_patch (semantic validation mismatch)** |
| `SUCCESS` | 8 | 16 | +8 | **recovery_patch_committed** |

## Final decision distribution

| decision | STRUCTEXPECT2_101215 | CANDPRIORITY1_RECOMPUTE |
|---|---|---|
| `reject` | 20 | 20 |
