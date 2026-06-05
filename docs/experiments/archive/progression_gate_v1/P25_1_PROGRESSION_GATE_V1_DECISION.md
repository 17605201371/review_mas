# P25.1 Progression Gate V1 Decision

- decision: **ROLLBACK**
- progression_gate_triggered_turns: 6
- broad_target_recovery_count: 2 -> 0
- fallback_target_recovery_count: 6 -> 5
- patch_emitted_count: 17 -> 2
- patch_committed_count: 6 -> 1
- rows_with_any_commit: 4 -> 1
- model_generated_commit_count: 2 -> 0
- system_salvaged_commit_count: 4 -> 1
- NO_EFFECT_PATCH: 1 -> 0
- BLOCKED_BY_POLICY: 27 -> 3
- canonical_regressions: NhLBhx5BVY

## Interpretation
- Progression Gate V1 does not satisfy the retention criteria; do not stack further changes on it without a root-cause review.
- The decision is based on gate actuation plus preservation of commits, rows with commits, salvage commits, and canonical stability.
- Config alignment passed before this compare was generated.
