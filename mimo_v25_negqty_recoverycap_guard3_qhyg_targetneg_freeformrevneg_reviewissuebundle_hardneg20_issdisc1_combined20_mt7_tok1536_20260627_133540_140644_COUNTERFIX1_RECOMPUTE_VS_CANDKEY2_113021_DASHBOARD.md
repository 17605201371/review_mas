# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_issdisc1_combined20_mt7_tok1536_20260627_133540_140644.jsonl` (label: COUNTERFIX1_RECOMPUTE, papers: 20)
- baseline:  `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_113021.jsonl` (label: CANDKEY2_113021, papers: 20)
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
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 88 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 86 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 64 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 41 | PASS |
| `final_support_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 61 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 82 | 75 | -7 |
| `evidence_json_status_turns` | 79 | 72 | -7 |
| `evidence_json_valid_turns` | 79 | 72 | -7 |
| `evidence_json_partial_recovered_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_turns` | 0 | 0 | 0 |
| `evidence_json_fallback_rate_pct` | 0 | 0 | 0 |
| `evidence_json_no_json_object_turns` | 0 | 0 | 0 |
| `evidence_json_invalid_json_turns` | 0 | 0 | 0 |
| `evidence_json_truncated_turns` | 0 | 0 | 0 |
| `evidence_json_prompt_chars_median` | 7826 | 7826 | 0 |
| `evidence_json_raw_chars_median` | 1436 | 2274 | +838 |
| `quote_bank_nonzero_turns` | 82 | 75 | -7 |
| `payload_evidence_item_total` | 135 | 155 | +20 |
| `evidence_agent_nonempty_payload_turns` | 64 | 55 | -9 |
| `evidence_agent_question_only_turns` | 3 | 0 | -3 |
| `first_support_fallback_turns` | 0 | 1 | +1 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 44 | 51 | +7 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `real_strong_support_total` | 71 | 88 | +17 |
| `independent_support_group_total` | 70 | 86 | +16 |
| `diagnostic_independent_support_group_total` | 86 | 119 | +33 |
| `claims_with_2plus_independent_or_diagnostic_support` | 31 | 51 | +20 |
| `empirical_real_strong_support_count` | 58 | 64 | +6 |
| `method_real_strong_support_count` | 13 | 24 | +11 |
| `table_or_figure_real_strong_support_count` | 32 | 43 | +11 |
| `result_or_experiment_real_strong_support_count` | 21 | 14 | -7 |
| `ablation_real_strong_support_count` | 5 | 7 | +2 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 20 | 37 | +17 |
| `moderate_diagnostic_support_total` | 20 | 37 | +17 |
| `moderate_absorbed_into_final_strong_count` | 32 | 53 | +21 |
| `moderate_remaining_diagnostic_count` | 20 | 37 | +17 |
| `diagnostic_support_signal_total` | 91 | 125 | +34 |
| `papers_with_real_strong_support` | 18 | 20 | +2 |
| `papers_with_empirical_support` | 18 | 19 | +1 |
| `papers_with_deep_support` | 18 | 19 | +1 |
| `positive_coverage_gap_papers` | 2 | 0 | -2 |
| `empirical_coverage_gap_papers` | 2 | 1 | -1 |
| `deep_support_gap_papers` | 2 | 1 | -1 |
| `claims_with_real_strong_support` | 40 | 55 | +15 |
| `claims_with_empirical_real_strong_support` | 35 | 39 | +4 |
| `claims_with_deep_support` | 37 | 41 | +4 |
| `claims_with_2plus_independent_support` | 22 | 29 | +7 |
| `primary_claim_total` | 59 | 60 | +1 |
| `primary_claims_with_real_strong_support` | 37 | 48 | +11 |
| `primary_claims_with_empirical_support` | 33 | 33 | 0 |
| `primary_claims_with_deep_support` | 35 | 35 | 0 |
| `zero_real_papers` | 2 | 0 | -2 |
| `final_support_total` | 71 | 88 | +17 |
| `final_support_direct_strong_count` | 39 | 35 | -4 |
| `final_support_promoted_from_medium_count` | 32 | 53 | +21 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 1 | 4 | +3 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 1 | 2 | +1 |
| `near_miss_promoted_to_final_count` | 0 | 1 | +1 |
| `support_trace_total` | 148 | 174 | +26 |
| `support_trace_included_count` | 71 | 88 | +17 |
| `support_trace_dropped_count` | 77 | 86 | +9 |
| `support_trace_hygiene_filtered_count` | 19 | 37 | +18 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 27 | 18 | -9 |
| `support_trace_semantic_mismatch_count` | 22 | 18 | -4 |
| `support_trace_duplicate_quote_count` | 7 | 13 | +6 |
| `support_trace_missing_verified_quote_count` | 1 | 0 | -1 |
| `final_support_specific_locator_count` | 48 | 61 | +13 |
| `final_support_weak_locator_count` | 23 | 27 | +4 |

## Negative & flaws

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 8 | 6 | -2 |
| `negative_evidence_candidate_raw_count` | 12 | 6 | -6 |
| `review_negative_verified_count` | 1 | 2 | +1 |
| `reviewer_absence_verified_count` | 7 | 4 | -3 |
| `reviewer_absence_verified_claim_count` | 12 | 4 | -8 |
| `reviewer_absence_verified_flaw_count` | 10 | 4 | -6 |
| `total_review_negative_verified_count` | 8 | 6 | -2 |
| `quote_grounded_review_issue_count` | 1 | 2 | +1 |
| `obligation_grounded_review_issue_count` | 7 | 4 | -3 |
| `obligation_grounded_review_issue_claim_count` | 7 | 3 | -4 |
| `reviewer_candidate_review_issue_count` | 4 | 4 | 0 |
| `reviewer_candidate_review_issue_claim_count` | 4 | 3 | -1 |
| `claim_obligation_review_issue_count` | 3 | 0 | -3 |
| `claim_obligation_review_issue_claim_count` | 3 | 0 | -3 |
| `verified_review_issue_count` | 8 | 6 | -2 |
| `verified_review_issue_claim_count` | 8 | 5 | -3 |
| `review_issue_bundle_count` | 7 | 4 | -3 |
| `review_issue_type_missing_ablation` | 1 | 1 | 0 |
| `review_issue_type_missing_baseline` | 0 | 0 | 0 |
| `review_issue_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `review_issue_type_insufficient_evaluation` | 1 | 2 | +1 |
| `review_issue_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `review_issue_type_evaluation_protocol_risk` | 1 | 1 | 0 |
| `review_issue_type_efficiency_cost_gap` | 2 | 0 | -2 |
| `review_issue_type_scope_overclaim` | 0 | 0 | 0 |
| `review_issue_type_result_claim_mismatch` | 0 | 0 | 0 |
| `review_issue_type_method_support_gap` | 1 | 0 | -1 |
| `review_issue_type_reproducibility_gap` | 1 | 0 | -1 |
| `paper_text_negative_candidate_count` | 22 | 13 | -9 |
| `author_limitation_only_count` | 2 | 1 | -1 |
| `prior_work_limitation_count` | 0 | 0 | 0 |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | 0 |
| `resource_or_scope_context_negative_candidate_count` | 0 | 0 | 0 |
| `semantic_negative_without_review_relation_count` | 0 | 0 | 0 |
| `semantic_negative_rejected_by_review_relation_count` | 1 | 3 | +2 |
| `scope_limitation_as_verified_negative_count` | 0 | 0 | 0 |
| `quote_bank_salvage_generated_negative_count` | 0 | 0 | 0 |
| `negative_evidence_linked_to_flaw_count` | 8 | 6 | -2 |
| `negative_evidence_linked_to_flaw_raw_count` | 12 | 6 | -6 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 12 | 5 | -7 |
| `verified_actionable_negative_flaw_count` | 12 | 5 | -7 |
| `verified_limitation_negative_flaw_count` | 0 | 0 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 1 | 0 | -1 |
| `negative_type_missing_ablation` | 1 | 2 | +1 |
| `negative_type_missing_baseline` | 0 | 0 | 0 |
| `negative_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `negative_type_insufficient_evaluation` | 1 | 3 | +2 |
| `negative_type_missing_robustness_or_generalization` | 0 | 0 | 0 |
| `negative_type_evaluation_protocol_risk` | 1 | 1 | 0 |
| `negative_type_efficiency_cost_gap` | 4 | 1 | -3 |
| `negative_type_reproducibility_gap` | 2 | 0 | -2 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 0 | 0 | 0 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 12 | 5 | -7 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 29 | 10 | -19 |
| `negative_grounding_conflict_count` | 14 | 4 | -10 |
| `invalid_negative_evidence_id_count_legacy` | 14 | 4 | -10 |
| `negative_semantic_anchor_conflict_count` | 14 | 4 | -10 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 1 | 1 | 0 |
| `downgraded_flaw_count` | 5 | 1 | -4 |
| `potential_concern_count` | 12 | 5 | -7 |
| `diagnosis_pending_potential_concern_count` | 99 | 76 | -23 |
| `diagnosis_pending_potential_concern_claim_count` | 53 | 45 | -8 |
| `diagnosis_pending_concern_recorded_count` | 2 | 4 | +2 |
| `diagnosis_pending_concern_recorded_claim_count` | 2 | 4 | +2 |
| `coverage_gap_potential_concern_count` | 25 | 12 | -13 |
| `reviewer_inferred_potential_concern_count` | 25 | 14 | -11 |
| `final_potential_concern_total` | 28 | 16 | -12 |
| `diagnosis_pending_type_missing_ablation` | 10 | 5 | -5 |
| `diagnosis_pending_type_missing_baseline` | 19 | 14 | -5 |
| `diagnosis_pending_type_unfair_or_weak_baseline` | 0 | 0 | 0 |
| `diagnosis_pending_type_insufficient_evaluation` | 21 | 18 | -3 |
| `diagnosis_pending_type_missing_robustness_or_generalization` | 6 | 0 | -6 |
| `diagnosis_pending_type_evaluation_protocol_risk` | 10 | 9 | -1 |
| `diagnosis_pending_type_efficiency_cost_gap` | 4 | 5 | +1 |
| `diagnosis_pending_type_reproducibility_gap` | 7 | 12 | +5 |
| `diagnosis_pending_type_scope_overclaim` | 8 | 3 | -5 |
| `diagnosis_pending_type_result_claim_mismatch` | 0 | 0 | 0 |
| `diagnosis_pending_type_method_support_gap` | 14 | 10 | -4 |

## Coverage gaps (deterministic · primary-claim · unsupported)

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `verified_coverage_gap_count` | 25 | 12 | -13 |
| `coverage_gap_potential_concern_count` | 25 | 12 | -13 |
| `reviewer_inferred_potential_concern_count` | 25 | 14 | -11 |
| `final_potential_concern_total` | 28 | 16 | -12 |
| `primary_claims_with_requirement_gaps` | 44 | 33 | -11 |

## State contamination

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `state_contamination_count` | 17 | 4 | -13 |
| `state_contamination_count_legacy` | 17 | 4 | -13 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 17 | 4 | -13 |
| `state_hygiene_warning_count` | 17 | 4 | -13 |
| `weak_target_warning_count` | 17 | 4 | -13 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 17 | 4 | -13 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 2 | 0 | -2 |
| `contamination_stale_gap_persistence` | 1 | 0 | -1 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 14 | 4 | -10 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 17 | 4 | -13 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `contested_support_total` | 19 | 7 | -12 |
| `contested_final_support_total` | 10 | 3 | -7 |
| `claims_with_contested_support` | 6 | 3 | -3 |
| `claims_with_contested_final_support` | 6 | 2 | -4 |
| `open_conflict_count` | 34 | 44 | +10 |
| `contested_relation_final_count` | 9 | 1 | -8 |
| `contested_relation_added_count` | 10 | 1 | -9 |
| `contested_relation_effective_count` | 9 | 1 | -8 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 2 | 0 | -2 |
| `diagnosis_pending_concern_commit_count` | 2 | 4 | +2 |
| `diagnosis_pending_concern_added_count` | 2 | 4 | +2 |
| `mark_contested_commit_count` | 10 | 1 | -9 |
| `mark_contested_with_positive_support_count` | 10 | 1 | -9 |
| `mark_contested_with_verified_negative_evidence_count` | 10 | 1 | -9 |
| `mark_contested_final_view_count` | 10 | 1 | -9 |
| `contested_relation_with_positive_support_count` | 9 | 1 | -8 |
| `contested_relation_with_verified_negative_evidence_count` | 9 | 1 | -8 |
| `contested_relation_final_view_count` | 9 | 1 | -8 |

## Gap cleanup & locator

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 17 | 12 | -5 |
| `evidence_gap_resolved_count` | 56 | 64 | +8 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 2 | 2 | 0 |
| `state_hygiene_open_gap_count` | 13 | 12 | -1 |
| `state_hygiene_stale_gap_count` | 4 | 0 | -4 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 17 | 12 | -5 |
| `targeted_open_gap_count` | 17 | 12 | -5 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 58 | 49 | -9 |
| `unresolved_open_raw_count` | 159 | 157 | -2 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 154 | 153 | -1 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 48 | 61 | +13 |
| `programmatic_weak_locator_count` | 23 | 27 | +4 |
| `programmatic_locator_type_table_count` | 17 | 20 | +3 |
| `programmatic_locator_type_figure_count` | 11 | 19 | +8 |
| `programmatic_locator_type_section_count` | 19 | 18 | -1 |
| `programmatic_locator_type_algorithm_count` | 1 | 2 | +1 |
| `programmatic_locator_type_theorem_count` | 0 | 2 | +2 |
| `programmatic_locator_type_generic_count` | 23 | 27 | +4 |
| `programmatic_high_confidence_locator_count` | 46 | 61 | +15 |
| `programmatic_low_confidence_locator_count` | 2 | 0 | -2 |

## Recovery

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `recovery_attempted` | 17 | 14 | -3 |
| `recovery_patch_validated` | 16 | 8 | -8 |
| `recovery_patch_committed` | 16 | 6 | -10 |
| `recovery_committed` | 16 | 6 | -10 |
| `recovery_success` | 16 | 6 | -10 |
| `hygiene_delta_improved` | 11 | 1 | -10 |
| `diagnosis_pending_recorded_layer` | 2 | 4 | +2 |
| `recovery_effective_repair` | 11 | 1 | -10 |
| `recovery_no_effect_commit` | 0 | 0 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 17 | 10 | -7 |
| `recovery_safe_resolution_or_clean_state` | 19 | 19 | 0 |
| `hygiene_delta_or_safe_block` | 12 | 5 | -7 |
| `hygiene_delta_or_safe_block_or_clean_state` | 17 | 19 | +2 |
| `recovery_safe_blocked_weak_target` | 0 | 4 | +4 |
| `recovery_safe_blocked_terminal_target` | 1 | 0 | -1 |
| `recovery_terminal_turns` | 1 | 0 | -1 |
| `recovery_repeat_allowed_false_turns` | 1 | 0 | -1 |
| `recovery_target_gate_real_target_turns` | 13 | 2 | -11 |
| `recovery_target_gate_negative_verified_target_turns` | 2 | 0 | -2 |
| `recovery_target_gate_diagnosis_pending_target_turns` | 2 | 4 | +2 |
| `recovery_target_gate_weak_target_turns` | 0 | 5 | +5 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 0 | 3 | +3 |
| `recovery_patch_operation_reject_patch_turns` | 1 | 8 | +7 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 3 | 1 | -2 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 1 | 0 | -1 |
| `recovery_patch_operation_mark_contested_turns` | 10 | 1 | -9 |
| `recovery_patch_operation_record_diagnosis_pending_concern_turns` | 2 | 4 | +2 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Recovery case audit

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `recovery_case_rows` | 18 | 15 | -3 |
| `recovery_case_audit_error_count` | 0 | 0 | 0 |
| `recovery_case_decision_hygiene_error_count` | 0 | 0 | 0 |
| `recovery_case_verified_review_negative_repair` | 1 | 0 | -1 |
| `recovery_case_verified_review_issue_repair` | 4 | 1 | -3 |
| `recovery_case_reviewer_inferred_negative_repair` | 0 | 0 | 0 |
| `recovery_case_verified_negative_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_verified_review_issue_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_reviewer_inferred_flaw_lifecycle_downgrade` | 0 | 0 | 0 |
| `recovery_case_state_hygiene_repair` | 0 | 0 | 0 |
| `recovery_case_assessment_limitation_routing` | 1 | 0 | -1 |
| `recovery_case_effective_repair_without_verified_negative` | 5 | 0 | -5 |
| `recovery_case_flaw_lifecycle_downgrade_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_effective_repair_needs_manual_review` | 0 | 0 | 0 |
| `recovery_case_attempted_not_committed` | 2 | 9 | +7 |
| `recovery_case_committed_not_effective` | 5 | 5 | 0 |
| `recovery_case_effective_repair_turns` | 11 | 1 | -10 |
| `recovery_case_effective_repair_not_verified_negative_repair` | 10 | 1 | -9 |
| `recovery_case_turns_with_verified_review_negative_evidence` | 1 | 0 | -1 |
| `recovery_case_turns_with_verified_review_issue_bundle_evidence` | 5 | 1 | -4 |
| `recovery_case_turns_with_reviewer_absence_audit_evidence` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_verified_review_negative` | 1 | 0 | -1 |
| `recovery_case_evidence_bucket_obligation_grounded_review_issue` | 5 | 1 | -4 |
| `recovery_case_evidence_bucket_reviewer_absence_audit` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_author_limitation_only` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_prior_work_limitation` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_positive_or_neutral_support` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_resource_or_scope_context` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_untrusted_model_output` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_quote-bank-negative-grounding_candidate` | 3 | 1 | -2 |
| `recovery_case_evidence_bucket_fallback-extraction_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_system_recovery_salvage_candidate` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_support_only` | 0 | 3 | +3 |
| `recovery_case_evidence_bucket_not_verified_or_unknown` | 0 | 0 | 0 |
| `recovery_case_evidence_bucket_missing_evidence_id` | 0 | 1 | +1 |

## Hygiene

| metric | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 1 | 6 | +5 | **safe_blocked_patch (policy restriction/abstention)** |
| `INSUFFICIENT_EVIDENCE` | 0 | 1 | +1 | **safe_blocked_patch (insufficient evidence criteria)** |
| `NO_EFFECT_PATCH` | 0 | 1 | +1 | **safe_blocked_patch (no state change needed)** |
| `SUCCESS` | 16 | 6 | -10 | **recovery_patch_committed** |

## Final decision distribution

| decision | CANDKEY2_113021 | COUNTERFIX1_RECOMPUTE |
|---|---|---|
| `reject` | 20 | 20 |
