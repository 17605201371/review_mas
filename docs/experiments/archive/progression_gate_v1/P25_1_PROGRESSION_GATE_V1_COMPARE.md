# P25.1 Progression Gate V1 Compare

## Aggregate Metrics
| Metric | Baseline | Progression Gate V1 |
| --- | ---: | ---: |
| progression_gate_triggered_turns | 0 | 6 |
| broad_target_gate_blocked | 0 | 0 |
| fallback_target_gate_blocked | 0 | 6 |
| weak_conflict_gate_blocked | 0 | 0 |
| recovery_enter_count | 34 | 5 |
| broad_target_recovery_count | 2 | 0 |
| fallback_target_recovery_count | 6 | 5 |
| weak_conflict_recovery_count | 0 | 0 |
| patch_emitted_count | 17 | 2 |
| patch_committed_count | 6 | 1 |
| rows_with_any_commit | 4 | 1 |
| model_generated_commit_count | 2 | 0 |
| system_salvaged_commit_count | 4 | 1 |
| NO_EFFECT_PATCH | 1 | 0 |
| BLOCKED_BY_POLICY | 27 | 3 |
| target_switch_count | 8 | 0 |
| early_finalize_count | 0 | 0 |
| avg_reward | 0.5443 | 0.5683 |
| decision_correct_rate | 0.9 | 0.9 |

## Per-Case Snapshot
| paper_id | bucket | baseline commits | gate commits | baseline emitted | gate emitted | baseline fallback recovery | gate fallback recovery | gate triggered | baseline reward | gate reward |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2Cg4YrsCMA | canonical_success_sensitive | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.5384 | 0.4244 |
| NhLBhx5BVY | canonical_success_sensitive | 1 | 0 | 2 | 0 | 0 | 0 | 0 | 0.5374 | 0.4839 |
| IqaQZ1Jdky | canonical_success_sensitive | 1 | 1 | 2 | 2 | 0 | 5 | 0 | 0.5825 | 0.5429 |
| kdriw2a8sl | canonical_success_sensitive | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.6439 | 0.6094 |
| hj323oR3rw | hardest_drift_prone | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0.2472 | 0.3542 |
| 9EBSEkFSje | hardest_drift_prone | 2 | 0 | 4 | 0 | 0 | 0 | 0 | 0.6410 | 0.7696 |
| Ze49bGd4ON | hardest_drift_prone | 0 | 0 | 5 | 0 | 6 | 0 | 0 | 0.4661 | 0.4971 |
| qgyF6JVmar | recovery_support | 0 | 0 | 1 | 0 | 0 | 0 | 6 | 0.5935 | 0.6305 |
| EXGahWDp1E | recovery_support | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.6499 | 0.7186 |
| meY36sGyyv | recovery_support | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0.5431 | 0.6524 |
