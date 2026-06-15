# Run comparison dashboard v1

- candidate: `mimo_v25_claimreq_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_144450.jsonl` (label: claimreq_144450, papers: 20)
- baseline:  `mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_003753.jsonl` (label: qhyg_003753, papers: 20)
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
| `real_strong_support_total` | `>=` | 16 | smoke scaled from 30/39 | 82 | PASS |
| `independent_support_group_total` | `>=` | 13 | smoke scaled from 24/39 | 82 | PASS |
| `empirical_real_strong_support_count` | `>=` | 11 | smoke scaled from 20/39 | 63 | PASS |
| `claims_with_deep_support` | `>=` | 5 | smoke scaled from 8/39 | 42 | PASS |
| `support_trace_missing_verified_quote_count` | `==` | 0 |  | 0 | PASS |
| `support_trace_overridden_by_negative_burden_count` | `==` | 0 |  | 0 | PASS |
| `evidence_formation_dead_loop_count` | `==` | 0 |  | 0 | PASS |
| `programmatic_specific_locator_count` | `>=` | 10 | smoke scaled from 18/39 | 62 | PASS |

**Overall protection: PASS**

## Evidence formation health

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `evidence_agent_worker_turns` | 93 | 94 | +1 |
| `quote_bank_nonzero_turns` | 93 | 94 | +1 |
| `payload_evidence_item_total` | 129 | 106 | -23 |
| `evidence_agent_nonempty_payload_turns` | 91 | 93 | +2 |
| `evidence_agent_question_only_turns` | 19 | 30 | +11 |
| `first_support_fallback_turns` | 38 | 33 | -5 |
| `model_adapter_quote_first_rewrite_count` | 0 | 0 | 0 |
| `model_adapter_strength_downgrade_count` | 0 | 0 | 0 |
| `small_model_quote_bank_augmentation_count` | 63 | 51 | -12 |
| `evidence_formation_dead_loop_count` | 0 | 0 | 0 |

## Positive support

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `real_strong_support_total` | 100 | 82 | -18 |
| `independent_support_group_total` | 100 | 82 | -18 |
| `diagnostic_independent_support_group_total` | 100 | 83 | -17 |
| `claims_with_2plus_independent_or_diagnostic_support` | 47 | 40 | -7 |
| `empirical_real_strong_support_count` | 76 | 63 | -13 |
| `method_real_strong_support_count` | 23 | 19 | -4 |
| `table_or_figure_real_strong_support_count` | 54 | 49 | -5 |
| `result_or_experiment_real_strong_support_count` | 20 | 13 | -7 |
| `ablation_real_strong_support_count` | 3 | 1 | -2 |
| `abstract_real_strong_support_count` | 0 | 0 | 0 |
| `verified_moderate_support_total` | 0 | 1 | +1 |
| `moderate_diagnostic_support_total` | 0 | 1 | +1 |
| `moderate_absorbed_into_final_strong_count` | 67 | 53 | -14 |
| `moderate_remaining_diagnostic_count` | 0 | 1 | +1 |
| `diagnostic_support_signal_total` | 100 | 83 | -17 |
| `papers_with_real_strong_support` | 20 | 20 | 0 |
| `papers_with_empirical_support` | 20 | 20 | 0 |
| `papers_with_deep_support` | 20 | 20 | 0 |
| `positive_coverage_gap_papers` | 0 | 0 | 0 |
| `empirical_coverage_gap_papers` | 0 | 0 | 0 |
| `deep_support_gap_papers` | 0 | 0 | 0 |
| `claims_with_real_strong_support` | 52 | 43 | -9 |
| `claims_with_empirical_real_strong_support` | 49 | 41 | -8 |
| `claims_with_deep_support` | 51 | 42 | -9 |
| `claims_with_2plus_independent_support` | 47 | 39 | -8 |
| `primary_claim_total` | 60 | 60 | 0 |
| `primary_claims_with_real_strong_support` | 45 | 41 | -4 |
| `primary_claims_with_empirical_support` | 42 | 39 | -3 |
| `primary_claims_with_deep_support` | 44 | 40 | -4 |
| `zero_real_papers` | 0 | 0 | 0 |
| `final_support_total` | 100 | 82 | -18 |
| `final_support_direct_strong_count` | 33 | 29 | -4 |
| `final_support_promoted_from_medium_count` | 67 | 53 | -14 |
| `final_support_semantic_weak_promotion_count` | 0 | 0 | 0 |
| `near_miss_deep_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_method_moderate_support_count` | 0 | 0 | 0 |
| `near_miss_specific_locator_moderate_count` | 0 | 0 | 0 |
| `near_miss_promoted_to_final_count` | 0 | 0 | 0 |
| `support_trace_total` | 102 | 84 | -18 |
| `support_trace_included_count` | 100 | 82 | -18 |
| `support_trace_dropped_count` | 2 | 2 | 0 |
| `support_trace_hygiene_filtered_count` | 0 | 1 | +1 |
| `support_trace_overridden_by_negative_burden_count` | 0 | 0 | 0 |
| `support_trace_weak_support_depth_count` | 2 | 0 | -2 |
| `support_trace_semantic_mismatch_count` | 0 | 1 | +1 |
| `support_trace_duplicate_quote_count` | 0 | 0 | 0 |
| `support_trace_missing_verified_quote_count` | 0 | 0 | 0 |
| `final_support_specific_locator_count` | 68 | 62 | -6 |
| `final_support_weak_locator_count` | 32 | 20 | -12 |

## Negative & flaws

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `negative_evidence_candidate_count` | 12 | 12 | 0 |
| `negative_evidence_linked_to_flaw_count` | 12 | 12 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |
| `verified_negative_flaw_count` | 12 | 11 | -1 |
| `verified_actionable_negative_flaw_count` | 8 | 7 | -1 |
| `verified_limitation_negative_flaw_count` | 4 | 4 | 0 |
| `negative_type_direct_contradiction` | 0 | 0 | 0 |
| `negative_type_negative_result` | 7 | 6 | -1 |
| `negative_type_missing_ablation` | 0 | 0 | 0 |
| `negative_type_missing_baseline` | 6 | 6 | 0 |
| `negative_type_insufficient_evaluation` | 0 | 0 | 0 |
| `negative_type_reproducibility_gap` | 0 | 0 | 0 |
| `negative_type_scope_overclaim` | 7 | 2 | -5 |
| `negative_type_result_claim_mismatch` | 0 | 0 | 0 |
| `negative_type_scope_limitation` | 6 | 7 | +1 |
| `synced_actionable_negative_type_count` | 0 | 0 | 0 |
| `negative_type_neutral_control_context` | 0 | 0 | 0 |
| `negative_type_generic_gap` | 0 | 0 | 0 |
| `verified_potential_concern_count` | 8 | 7 | -1 |
| `grounded_weakness_count` | 0 | 0 | 0 |
| `assessment_limitation_flaw_count` | 7 | 5 | -2 |
| `negative_grounding_conflict_count` | 0 | 0 | 0 |
| `invalid_negative_evidence_id_count_legacy` | 0 | 0 | 0 |
| `negative_semantic_anchor_conflict_count` | 0 | 0 | 0 |
| `generic_gap_semantic_rejected_count` | 0 | 0 | 0 |
| `negative_evidence_semantic_rejected_count` | 3 | 0 | -3 |
| `downgraded_flaw_count` | 3 | 0 | -3 |
| `potential_concern_count` | 8 | 7 | -1 |

## State contamination

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `state_contamination_count` | 0 | 1 | +1 |
| `state_contamination_count_legacy` | 0 | 1 | +1 |
| `harmful_state_contamination_count` | 0 | 0 | 0 |
| `repairable_state_warning_count` | 0 | 0 | 0 |
| `conservative_state_warning_count` | 0 | 1 | +1 |
| `state_hygiene_warning_count` | 0 | 1 | +1 |
| `weak_target_warning_count` | 0 | 1 | +1 |
| `repairable_contamination_target_count` | 0 | 0 | 0 |
| `conservative_contamination_target_count` | 0 | 1 | +1 |
| `blocked_fallback_contamination_target_count` | 0 | 0 | 0 |
| `blocked_empty_contamination_target_count` | 0 | 0 | 0 |
| `contamination_unsupported_with_strong_support` | 0 | 0 | 0 |
| `contamination_zero_real_support` | 0 | 0 | 0 |
| `contamination_stale_gap_persistence` | 0 | 1 | +1 |
| `contamination_unsupported_flaw_escalation` | 0 | 0 | 0 |
| `contamination_negative_evidence_overclaim` | 0 | 0 | 0 |
| `contamination_evidence_misbinding` | 0 | 0 | 0 |
| `contamination_meta_leakage` | 0 | 0 | 0 |
| `contamination_stale_flaw_persistence` | 0 | 0 | 0 |
| `contamination_harmful_recovery_risk` | 0 | 0 | 0 |
| `target_gate_real_target` | 0 | 0 | 0 |
| `target_gate_weak_target` | 0 | 1 | +1 |
| `target_gate_fallback_target` | 0 | 0 | 0 |
| `target_gate_empty_target` | 0 | 0 | 0 |

## Contested support

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `contested_support_total` | 14 | 14 | 0 |
| `contested_final_support_total` | 14 | 13 | -1 |
| `claims_with_contested_support` | 7 | 7 | 0 |
| `claims_with_contested_final_support` | 7 | 7 | 0 |
| `open_conflict_count` | 0 | 0 | 0 |
| `contested_relation_final_count` | 8 | 6 | -2 |
| `contested_relation_added_count` | 8 | 6 | -2 |
| `contested_relation_effective_count` | 8 | 6 | -2 |
| `conflict_to_contested_resolution_count` | 0 | 0 | 0 |
| `negative_verified_target_preserved_count` | 11 | 13 | +2 |
| `mark_contested_commit_count` | 8 | 6 | -2 |
| `mark_contested_with_positive_support_count` | 8 | 6 | -2 |
| `mark_contested_with_verified_negative_evidence_count` | 8 | 6 | -2 |
| `mark_contested_final_view_count` | 8 | 6 | -2 |
| `contested_relation_with_positive_support_count` | 8 | 6 | -2 |
| `contested_relation_with_verified_negative_evidence_count` | 8 | 6 | -2 |
| `contested_relation_final_view_count` | 8 | 6 | -2 |

## Gap cleanup & locator

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `evidence_gap_open_count` | 1 | 6 | +5 |
| `evidence_gap_resolved_count` | 49 | 44 | -5 |
| `evidence_gap_superseded_count` | 0 | 0 | 0 |
| `evidence_gap_not_assessable_count` | 20 | 28 | +8 |
| `state_hygiene_open_gap_count` | 1 | 5 | +4 |
| `state_hygiene_stale_gap_count` | 0 | 1 | +1 |
| `targetless_open_gap_count` | 0 | 0 | 0 |
| `meta_or_context_open_gap_count` | 0 | 0 | 0 |
| `actionable_targeted_open_gap_count` | 0 | 0 | 0 |
| `diagnostic_targeted_open_gap_count` | 1 | 6 | +5 |
| `targeted_open_gap_count` | 1 | 6 | +5 |
| `assessment_limitation_open_gap_count` | 0 | 0 | 0 |
| `unresolved_open_count` | 10 | 9 | -1 |
| `unresolved_open_raw_count` | 56 | 56 | 0 |
| `unresolved_resolved_count` | 0 | 0 | 0 |
| `unresolved_deferred_count` | 56 | 55 | -1 |
| `targetless_unresolved_deferred_count` | 0 | 0 | 0 |
| `programmatic_specific_locator_count` | 68 | 62 | -6 |
| `programmatic_weak_locator_count` | 32 | 20 | -12 |
| `programmatic_locator_type_table_count` | 20 | 23 | +3 |
| `programmatic_locator_type_figure_count` | 22 | 17 | -5 |
| `programmatic_locator_type_section_count` | 23 | 18 | -5 |
| `programmatic_locator_type_algorithm_count` | 0 | 4 | +4 |
| `programmatic_locator_type_theorem_count` | 3 | 0 | -3 |
| `programmatic_locator_type_generic_count` | 32 | 20 | -12 |
| `programmatic_high_confidence_locator_count` | 68 | 62 | -6 |
| `programmatic_low_confidence_locator_count` | 0 | 0 | 0 |

## Recovery

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `recovery_attempted` | 15 | 16 | +1 |
| `recovery_patch_validated` | 9 | 8 | -1 |
| `recovery_patch_committed` | 9 | 7 | -2 |
| `recovery_committed` | 9 | 7 | -2 |
| `recovery_success` | 9 | 7 | -2 |
| `hygiene_delta_improved` | 8 | 6 | -2 |
| `recovery_effective_repair` | 8 | 6 | -2 |
| `recovery_no_effect_commit` | 1 | 1 | 0 |
| `recovery_harmful_commit_risk` | 0 | 0 | 0 |
| `recovery_safe_resolution` | 12 | 14 | +2 |
| `recovery_safe_resolution_or_clean_state` | 20 | 20 | 0 |
| `hygiene_delta_or_safe_block` | 11 | 13 | +2 |
| `hygiene_delta_or_safe_block_or_clean_state` | 20 | 20 | 0 |
| `recovery_safe_blocked_weak_target` | 0 | 1 | +1 |
| `recovery_safe_blocked_terminal_target` | 3 | 6 | +3 |
| `recovery_terminal_turns` | 6 | 7 | +1 |
| `recovery_repeat_allowed_false_turns` | 6 | 7 | +1 |
| `recovery_target_gate_real_target_turns` | 4 | 2 | -2 |
| `recovery_target_gate_negative_verified_target_turns` | 11 | 13 | +2 |
| `recovery_target_gate_weak_target_turns` | 0 | 1 | +1 |
| `recovery_target_gate_fallback_target_turns` | 0 | 0 | 0 |
| `recovery_target_gate_empty_target_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_reject_patch_turns` | 6 | 9 | +3 |
| `recovery_patch_operation_downgrade_final_to_candidate_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_route_to_assessment_limitation_turns` | 0 | 0 | 0 |
| `recovery_patch_operation_downgrade_claim_to_unsupported_turns` | 1 | 1 | 0 |
| `recovery_patch_operation_mark_contested_turns` | 8 | 6 | -2 |
| `recovery_patch_operation_resolve_stale_gap_turns` | 0 | 0 | 0 |

## Hygiene

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---|---|---|
| `final_nonreal_strong_support` | 0 | 0 | 0 |
| `low_score_promoted_strong` | 0 | 0 | 0 |
| `final_report_leakage_paper_count` | 0 | 0 | 0 |
| `user_report_leakage_paper_count` | 0 | 0 | 0 |
| `synthetic_marker_in_supporting_count` | 0 | 0 | 0 |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | 0 |

## Recovery failure codes

| code | qhyg_003753 | claimreq_144450 | delta | interpreted safety outcome |
|---|---|---|---|---|
| `BLOCKED_BY_POLICY` | 6 | 8 | +2 | **safe_blocked_patch (policy restriction/abstention)** |
| `EVIDENCE_SEMANTIC_MISMATCH` | 0 | 1 | +1 | **safe_blocked_patch (semantic evidence validation mismatch)** |
| `SUCCESS` | 9 | 7 | -2 | **recovery_patch_committed** |

## Final decision distribution

| decision | qhyg_003753 | claimreq_144450 |
|---|---|---|
| `accept` | 12 | 5 |
| `reject` | 8 | 15 |

