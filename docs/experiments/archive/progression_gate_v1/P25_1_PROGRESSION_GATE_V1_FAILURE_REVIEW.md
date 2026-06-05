# P25.1 Progression Gate V1 Failure Review

## Result

Final run after two implementation fixes:

- config alignment: PASS
- rows: 10/10
- gate triggered: 6 turns
- dominant gate reason: fallback target
- decision: ROLLBACK

## Metrics

| Metric | Baseline | Gate V1 |
| --- | ---: | ---: |
| progression_gate_triggered_turns | 0 | 6 |
| recovery_enter_count | 34 | 5 |
| broad_target_recovery_count | 2 | 0 |
| fallback_target_recovery_count | 6 | 5 |
| patch_emitted_count | 17 | 2 |
| patch_committed_count | 6 | 1 |
| rows_with_any_commit | 4 | 1 |
| model_generated_commit_count | 2 | 0 |
| system_salvaged_commit_count | 4 | 1 |
| NO_EFFECT_PATCH | 1 | 0 |
| BLOCKED_BY_POLICY | 27 | 3 |
| decision_correct_rate | 0.9 | 0.9 |

## Implementation Bugs Found And Fixed During This Round

### 1. Gate fields were dropped by manager normalization

`normalize_manager_payload(...)` did not preserve the new `progression_gate_*` fields, so the first compare showed `policy_source=progression_gate_override` but `progression_gate_triggered_turns=0`.

Fix applied:

- added gate fields to `normalize_manager_payload(...)`
- added gate fields to `build_turn_log(...)`

### 2. Gate downgrade was overwritten by recovery phase protocol

The first valid gate pass downgraded `challenge_previous_hypothesis` to `verify_evidence`, but `_apply_recovery_phase_protocol(...)` immediately re-promoted some gated turns back into `request_evidence_recheck` because unresolved conflict still existed.

Fix applied:

- when `progression_gate_triggered=True` and the action has already been safely downgraded to non-recovery, recovery phase protocol now respects the gate and does not re-promote the same turn.

### 3. Safe downgrade initially allowed `extract_claims`

The first run allowed gate fallback to return `extract_claims`, causing repeated claim extraction in later turns.

Fix applied:

- safe action now prefers `verify_evidence`, then `analyze_flaws`; it no longer treats `extract_claims` as a preferred safe continuation once claims exist.

## Why Final Result Is Still Negative

Gate V1 blocks aggressive recovery, but it does not create a better target.

The clearest case is `qgyF6JVmar`:

- gate triggered 6 times
- all were fallback-target blocks
- recovery turns dropped to 0
- patch emissions dropped to 0
- commits remained 0

This means Gate V1 successfully suppresses the bad recovery path, but the system has no compensating path that turns `claim-fallback-1` into a real claim target. It prevents a bad patch route, but also removes patch/salvage opportunities.

The broader failure is visible in aggregate:

- recovery turns collapse: 34 -> 5
- patch emissions collapse: 17 -> 2
- commits collapse: 6 -> 1
- salvage commits collapse: 4 -> 1

Gate V1 is therefore too suppressive as a standalone change.

## Important Observation

Several samples regressed even without gate trigger:

- `NhLBhx5BVY`: baseline commit 1 -> gate run commit 0, gate triggered 0
- `9EBSEkFSje`: baseline commit 2 -> gate run commit 0, gate triggered 0
- `meY36sGyyv`: baseline commit 2 -> gate run commit 0, gate triggered 0

This means full 10-row 9B comparisons at `temperature=0.2` are too expensive and noisy for rapid mechanism debugging. They are still necessary for final decisions, but not for every micro-iteration.

## Root Cause

Progression Gate V1 is acting as a brake, not a target repair mechanism.

It can block fallback/broad recovery, but it cannot convert weak/fallback targets into high-quality targets. Without a paired fallback restraint or target repair path, blocking recovery mostly reduces emissions and commits.

## Next Debug Adjustment

Before another full 10-row run, use a 4-row smoke subset:

- `qgyF6JVmar`: gate-hit fallback loop case
- `IqaQZ1Jdky`: fallback recovery with one commit retained
- `NhLBhx5BVY`: canonical regression without gate trigger
- `9EBSEkFSje` or `meY36sGyyv`: baseline success lost without gate trigger

Use the smoke subset only for mechanism debugging. Once the mechanism is sane, rerun the full fixed 10-row forensic subset.

## Direction

Do not keep Gate V1 as-is.

The next code change should not be a stronger gate. The next useful change is either:

1. make gate one-shot and non-repeating per fallback target, or
2. implement the previously identified `Fallback Restraint v1`, which prevents fallback claims from becoming primary recovery anchors in the first place.

Given the target-evolution audit, `Fallback Restraint v1` remains the more principled next cut.
