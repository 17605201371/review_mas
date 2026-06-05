# P25.1 Iteration Subset

- fixed_subset: `outputs/results_main/review_infer/p25_1_iteration_subset.parquet`
- fixed_count: 10
- note: target sticky round reuses the exact same subset as the retained explicit recovery-phase baseline.

## Fixed Cases
- `2Cg4YrsCMA` [canonical_success_sensitive]: canonical success-sensitive; previously commits but is vulnerable to policy / trajectory changes
- `NhLBhx5BVY` [canonical_success_sensitive]: canonical success-sensitive; high emission with blocked recovery behavior
- `IqaQZ1Jdky` [canonical_success_sensitive]: canonical success-sensitive; canonical model-generated recovery commit path
- `kdriw2a8sl` [canonical_success_sensitive]: canonical success-sensitive; recovery-relevant but easy to regress into blocked-only behavior
- `hj323oR3rw` [hardest_drift_prone]: hardest drift-prone sentinel; stress test for recovery retention without obvious regression
- `9EBSEkFSje` [hardest_drift_prone]: hardest drift-prone; often falls back to non-recovery trajectory and early consolidation
- `Ze49bGd4ON` [hardest_drift_prone]: hardest / drift-prone with recovery patch emission and a successful commit in the 9B baseline
- `qgyF6JVmar` [recovery_support]: support case with successful recovery commit; helps detect whether explicit phase hurts already-good emission
- `EXGahWDp1E` [recovery_support]: support case with emitted but blocked patches; useful for watching emission stability without forced success
- `meY36sGyyv` [recovery_support]: support case with both repeated emission and at least one commit; useful for retention and early-finalize checks
