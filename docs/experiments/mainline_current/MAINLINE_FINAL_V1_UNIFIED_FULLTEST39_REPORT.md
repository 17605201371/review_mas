# Mainline-Final-v1 Unified Fulltest39 Report

## 总结论

当前系统已经具备较稳定的 evidence binding、fallback flaw guard、final-view hard-negative lifecycle 和 report 分区展示。正式主试验前的剩余工作不是继续新增 controller，而是冻结统一指标口径，并将 accept/reject 仅作为 health check；论文主线应报告 support quality、criterion grounding、hard-negative lifecycle 与 final-view report hygiene。

## Runtime Decision Health

| metric | value |
| --- | --- |
| accuracy | 0.7692 |
| macro_f1 | 0.4348 |
| accept_recall | 0.0 |
| reject_recall | 1.0 |
| predicted_accept_count | 0 |
| false_accept_ids | 无 |
| recovered_accept_ids | 无 |

## Evidence / Support Quality

| metric | value |
| --- | --- |
| real_strong_support_total | 28 |
| nonabstract_strong_support_total | 27 |
| empirical_strong_support_total | 21 |
| method_strong_support_total | 6 |
| table_or_figure_strong_support_total | 0 |
| fallback_strong_support_total | 0 |
| strong_support_binding_precision | 1.0 |
| rows_with_2plus_real_strong_support | 7 |
| accept_rows_with_2plus_real_strong_support | 2 |

## State / Recovery / Runtime Hygiene

| metric | value |
| --- | --- |
| unresolved_count | 190 |
| evidence_gap_count | 147 |
| flaw_count | 51 |
| patch_emitted_count | 109 |
| patch_committed_count | 6 |
| rows_with_any_commit | 6 |
| evidence_json_invalid_or_missing_count | 27 |
| evidence_json_fallback_used_count | 4 |
| legacy_controller_active_turns | 0 |

## Final-View Unresolved / Candidate-Flaw Classifier

| metric | value |
| --- | --- |
| view_counts | {'not_assessable': 26, 'borderline_insufficient': 6, 'reject_like': 5, 'borderline_positive': 1, 'accept_like': 1} |
| accuracy | 0.7949 |
| macro_f1 | 0.5412 |
| accept_recall | 0.1111 |
| reject_recall | 1.0 |
| false_accept_ids | 无 |
| recovered_accept_ids | LebzzClHYw |

## Final-View Report Renderer

| metric | value |
| --- | --- |
| rows | 39 |
| classifier_view_counts | {'not_assessable': 26, 'borderline_insufficient': 6, 'reject_like': 5, 'borderline_positive': 1, 'accept_like': 1} |
| confirmed_weakness_meta_leak_rows | 0 |
| reports_with_confirmed_weakness | 1 |
| reports_with_potential_concerns | 6 |
| reports_with_review_limitations | 35 |
| reports_with_unresolved_questions | 39 |
| section_totals | {'confirmed_weaknesses': 2, 'potential_concerns': 11, 'review_limitations': 90, 'unresolved_questions': 187, 'resolved_or_stale_items': 72, 'minor_or_nonblocking_flaws': 3} |

## Method / Soundness Gap Audit

| metric | value |
| --- | --- |
| total_rows | 39 |
| gold_accept_count | 9 |
| gold_reject_count | 30 |
| accept_like_count | 0 |
| borderline_positive_count | 5 |
| runtime_false_accept_ids | [] |
| runtime_false_reject_ids | ['hj323oR3rw', 'QAAsnSRwgu', 'X41c4uB4k0', 'gzqrANCF4g', 'KI9NqjLVDT', '1HCN4pjTb4', 'LebzzClHYw', 'BXY6fe7q31', 'jVEoydFOl9'] |
| gold_accept_gap_counts | {'real_strong_lt3': 8, 'nonabstract_lt3': 8, 'no_empirical_support': 5, 'no_method_support': 8, 'independent_lt3': 8, 'unresolved_gt4': 4, 'novelty_not_positive': 8, 'soundness_not_positive': 8, 'empirical_not_positive': 5, 'trusted_major_or_critical_flaw_present': 1} |
| borderline_gap_counts | {'real_strong_lt3': 3, 'nonabstract_lt3': 3, 'no_method_support': 2, 'independent_lt3': 4, 'novelty_not_positive': 2, 'soundness_not_positive': 2, 'unresolved_gt4': 3, 'trusted_major_or_critical_flaw_present': 1} |
| gold_accept_blocker_families | {'hard_negative_burden': 5, 'method_soundness_gap': 3, 'support_depth_gap': 1} |
| borderline_blocker_families | {'method_soundness_gap': 1, 'support_depth_gap': 1, 'hard_negative_burden': 3} |
| gold_accept_with_method_support | 1 |
| gold_accept_with_soundness_positive | 1 |
| gold_accept_with_novelty_positive | 1 |
| borderline_with_method_support | 3 |
| borderline_with_soundness_positive | 3 |

## Recommendation Policy Simulation

| rule | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_current | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |
| support_count_real_ge2 | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | uOrfve3prk, 9zEBK3E9bX, QAgwFiIY4p, TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw, BXY6fe7q31 |
| support_quality_basic | 0.7179 | 0.546 | 0.2222 | 0.8667 | 6 | 9zEBK3E9bX, QAgwFiIY4p, TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw, BXY6fe7q31 |
| method_plus_result | 0.7436 | 0.5076 | 0.1111 | 0.9333 | 3 | TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw |
| criterion_positive | 0.7436 | 0.5647 | 0.2222 | 0.9 | 5 | 9zEBK3E9bX, TPAj63ax4Y, ZHr0JajZfH | LebzzClHYw, BXY6fe7q31 |
| high_precision_criterion_quality | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 无 | 无 |

## 当前判断

这轮统一表确认：系统已有可解释的 final-view report 与高精度 conservative recommendation view，但 runtime 二分类仍不能作为主指标。下一步应做正式主试验前的 9B 小确认或 9B fulltest dry run，前提是固定本表中的指标口径，不再新增 sticky/throttle/gate 类 runtime controller。
