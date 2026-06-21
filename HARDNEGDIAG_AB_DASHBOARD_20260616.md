# Run comparison dashboard v1

- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_hardnegdiag_hardneg20_mt7_b4w2_api1_r10t600_20260616_184705.jsonl` (label: hardnegdiag_on, papers: 20)
- baseline:  `mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_mt7_b4w2_api2_r8t600_20260616_172713_merged20.jsonl` (label: qhyg_base, papers: 20)
- dashboard_mode: `smoke`

## Protection lines

| metric | op | threshold | note | actual | pass |
|---|---|---|---|---|---|
| `final_nonreal_strong_support` | `==` | 0 |  | 0 | PASS |
| `low_score_promoted_strong` | `==` | 0 |  | 0 | PASS |
| `final_report_leakage_paper_count` | `==` | 0 |  | 0 | PASS |
| `synthetic_marker_in_supporting_count` | `==` | 0 |  | 0 | PASS |
| `negative_evidence_unlinked_to_flaw` | `==` | 0 |  | 0 | PASS |
| `recovery_safe_resolution_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `hygiene_delta_or_safe_block_or_clean_state` | `>=` | 11 | smoke scaled from 20/39 | 20 | PASS |
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 53 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 53 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 41 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 26 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 42 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 81 | 31 | -50 |
| `quote_bank_nonzero_turns` | 81 | 31 | -50 |
| `payload_evidence_item_total` | 97 | 55 | -42 |
| `evidence_agent_nonempty_payload_turns` | 78 | 30 | -48 |
| `evidence_agent_question_only_turns` | 28 | 3 | -25 |
| `first_support_fallback_turns` | 31 | 24 | -7 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 43 | 28 | -15 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `real_strong_support_total` | 75 | 53 | -22 |
| `independent_support_group_total` | 75 | 53 | -22 |
| `diagnostic_independent_support_group_total` | 76 | 53 | -23 |
| `claims_with_2plus_independent_or_diagnostic_support` | 37 | 26 | -11 |
| `empirical_real_strong_support_count` | 58 | 41 | -17 |
| `method_real_strong_support_count` | 17 | 12 | -5 |
| `table_or_figure_real_strong_support_count` | 46 | 38 | -8 |
| `result_or_experiment_real_strong_support_count` | 11 | 3 | -8 |
| `ablation_real_strong_support_count` | 1 | 0 | -1 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 2 | 0 | -2 |
| `moderate_diagnostic_support_total` | 2 | 0 | -2 |
| `moderate_absorbed_into_final_strong_count` | 55 | 39 | -16 |
| `moderate_remaining_diagnostic_count` | 2 | 0 | -2 |
| `diagnostic_support_signal_total` | 77 | 53 | -24 |
| `papers_with_real_strong_support` | 20 | 20 | 0 |
| `papers_with_empirical_support` | 20 | 20 | 0 |
| `papers_with_deep_support` | 20 | 20 | 0 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 0 | 0 | 0 |
| `deep_support_gap_papers` | 0 | 0 | 0 |
| `claims_with_real_strong_support` | 39 | 26 | -13 |
| `claims_with_empirical_real_strong_support` | 37 | 25 | -12 |
| `claims_with_deep_support` | 38 | 26 | -12 |
| `claims_with_2plus_independent_support` | 36 | 26 | -10 |
| `primary_claim_total` | 60 | 60 | 0 |
| `primary_claims_with_real_strong_support` | 33 | 25 | -8 |
| `primary_claims_with_empirical_support` | 31 | 24 | -7 |
| `primary_claims_with_deep_support` | 32 | 25 | -7 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 75 | 53 | -22 |
| `final_support_direct_strong_count` | 20 | 14 | -6 |
| `final_support_promoted_from_medium_count` | 55 | 39 | -16 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_method_moderate_support_count` | 1 | 0 | -1 |
| `near_miss_specific_locator_moderate_count` | 1 | 0 | -1 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 79 | 53 | -26 |
| `support_trace_included_count` | 75 | 53 | -22 |
| `support_trace_dropped_count` | 4 | 0 | -4 |
| `support_trace_hygiene_filtered_count` | 3 | 0 | -3 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 1 | 0 | -1 |
| `support_trace_semantic_mismatch_count` | 0 | 0 | 0 |
| `support_trace_duplicate_quote_count` | 0 | 0 | 0 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 51 | 42 | -9 |
| `final_support_weak_locator_count` | 24 | 11 | -13 |

## Negative & flaws

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 4 | 0 | -4 |
| `negative_evidence_linked_to_flaw_count` | 4 | 0 | -4 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 4 | 0 | -4 |
| `verified_actionable_negative_flaw_count` | 3 | 0 | -3 |
| `verified_limitation_negative_flaw_count` | 1 | 0 | -1 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 0 | 0 | 0 |
| `negative_type_missing_ablation` | 0 | 0 | 0 |
| `negative_type_missing_baseline` | 6 | 0 | -6 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_overclaim` | 0 | 0 | 0 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 4 | 1 | -3 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 3 | 0 | -3 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 2 | 1 | -1 |
| `negative_grounding_conflict_count` | 0 | 0 | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 | 0 | 0 |
| `negative_semantic_anchor_conflict_count` | 0 | 0 | 0 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 0 | 0 | 0 |
| `downgraded_flaw_count` | 0 | 0 | 0 |
| `potential_concern_count` | 3 | 0 | -3 |

## State contamination

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `state_contamination_count` | 1 | 0 | -1 |
| `state_contamination_count_legacy` | 1 | 0 | -1 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 1 | 0 | -1 |
| `state_hygiene_warning_count` | 1 | 0 | -1 |
| `weak_target_warning_count` | 1 | 0 | -1 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 1 | 0 | -1 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 0 | 0 |
| `contamination_stale_gap_persistence` | 1 | 0 | -1 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 0 | 0 | 0 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 1 | 0 | -1 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `contested_support_total` | 2 | 0 | -2 |
| `contested_final_support_total` | 2 | 0 | -2 |
| `claims_with_contested_support` | 1 | 0 | -1 |
| `claims_with_contested_final_support` | 1 | 0 | -1 |
| `open_conflict_count` | 0 | 0 | 0 |
| `contested_relation_final_count` | 3 | 0 | -3 |
| `contested_relation_added_count` | 3 | 0 | -3 |
| `contested_relation_effective_count` | 3 | 0 | -3 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 3 | 0 | -3 |
| `mark_contested_commit_count` | 3 | 0 | -3 |
| `mark_contested_with_positive_support_count` | 3 | 0 | -3 |
| `mark_contested_with_verified_negative_evidence_count` | 3 | 0 | -3 |
| `mark_contested_final_view_count` | 3 | 0 | -3 |
| `contested_relation_with_positive_support_count` | 3 | 0 | -3 |
| `contested_relation_with_verified_negative_evidence_count` | 3 | 0 | -3 |
| `contested_relation_final_view_count` | 3 | 0 | -3 |

## Gap cleanup & locator

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 8 | 2 | -6 |
| `evidence_gap_resolved_count` | 39 | 26 | -13 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 28 | 45 | +17 |
| `state_hygiene_open_gap_count` | 7 | 2 | -5 |
| `state_hygiene_stale_gap_count` | 1 | 0 | -1 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 8 | 2 | -6 |
| `targeted_open_gap_count` | 8 | 2 | -6 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 10 | 6 | -4 |
| `unresolved_open_raw_count` | 59 | 53 | -6 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 59 | 51 | -8 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 51 | 42 | -9 |
| `programmatic_weak_locator_count` | 24 | 11 | -13 |
| `programmatic_locator_type_table_count` | 16 | 15 | -1 |
| `programmatic_locator_type_figure_count` | 19 | 18 | -1 |
| `programmatic_locator_type_section_count` | 15 | 9 | -6 |
| `programmatic_locator_type_algorithm_count` | 0 | 0 | 0 |
| `programmatic_locator_type_theorem_count` | 1 | 0 | -1 |
| `programmatic_locator_type_generic_count` | 24 | 11 | -13 |
| `programmatic_high_confidence_locator_count` | 51 | 42 | -9 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `recovery_attempted` | 4 | 0 | -4 |
| `recovery_patch_validated` | 4 | 0 | -4 |
| `recovery_patch_committed` | 4 | 0 | -4 |
| `recovery_committed` | 4 | 0 | -4 |
| `recovery_success` | 4 | 0 | -4 |
| `hygiene_delta_improved` | 3 | 0 | -3 |
| `recovery_effective_repair` | 3 | 0 | -3 |
| `recovery_no_effect_commit` | 1 | 0 | -1 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 4 | 0 | -4 |
| `recovery_safe_resolution_or_clean_state` | 20 | 20 | 0 |
| `hygiene_delta_or_safe_block` | 3 | 0 | -3 |
| `hygiene_delta_or_safe_block_or_clean_state` | 19 | 20 | +1 |
| `recovery_safe_blocked_weak_target` | 0 | 0 | 0 |
| `recovery_safe_blocked_terminal_target` | 0 | 0 | 0 |
| `recovery_terminal_turns` | 0 | 0 | 0 |
| `recovery_repeat_allowed_false_turns` | 0 | 0 | 0 |
| `recovery_target_gate_real_target_turns` | 1 | 0 | -1 |
| `recovery_target_gate_negative_verified_target_turns` | 3 | 0 | -3 |
| `recovery_target_gate_weak_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_reject_patch_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 1 | 0 | -1 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 3 | 0 | -3 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Hygiene

| metric | qhyg_base | hardnegdiag_on | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | qhyg_base | hardnegdiag_on | delta | interpreted safety outcome |
|---|---|---|---|---|
| `SUCCESS` | 4 | 0 | -4 | **recovery_patch_committed** |

## Final decision distribution

| decision | qhyg_base | hardnegdiag_on |
|---|---|---|
| `accept` | 9 | 2 |
| `reject` | 11 | 18 |

