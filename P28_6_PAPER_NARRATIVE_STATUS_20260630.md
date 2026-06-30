# P28.6 Paper Narrative Status

Date: 2026-06-30

## Current Claim

The defensible paper narrative is not "the system finds many copied negative quotes." Direct quote-grounded reviewer negatives remain at `review_negative_verified_count=0`.

The stronger narrative is:

> DrMAS verifies reviewer-proposed issues as ReviewState objects by checking claim anchors, observed paper inventory, concrete missing or mismatched entities, counterevidence, and non-destructive recovery. This separates direct quote-grounded negatives from obligation-grounded review issues.

## Authoritative Results

### P28.6 ConflictFix TargetRefine2 Offline Recompute

Artifacts:

- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_AUDIT.json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`

Metrics:

- `paper_count=20`
- `review_negative_verified_count=0`
- `verified_review_issue_count=13`
- `verified_review_issue_cluster_count=9`
- `duplicate_review_issue_row_count=4`
- `reviewer_candidate_review_issue_count=13`
- `reviewer_candidate_review_issue_critique_payload_count=2`
- `reviewer_candidate_review_issue_deterministic_seed_count=11`
- `claim_obligation_review_issue_count=0`
- `verified_missing_ablation_cluster_count=6`
- `mark_contested_commit_count=14`
- `recovery_case_verified_review_issue_repair=6`
- `negative_grounding_conflict_count=0`
- `negative_semantic_anchor_conflict_count=0`
- `semantic_negative_without_review_relation_count=0`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- protection: PASS

Manual audit from TargetRefine2 still applies unless the case table changes: 9 system clusters, 8/9 judged A/B, with the weak C cluster being `number_motion_components_beyond`.

Paper-facing wording:

> On hardneg20, the current verifier produces 9 obligation-grounded review issue clusters; manual audit judged 8/9 clusters as valid or defensible. The direct quote-grounded negative lane remains strict and did not produce verified direct negatives.

### P28.6 Fresh MiMo Partial16 Recompute

Artifacts:

- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_AUDIT.json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_RECOVERY_CASE_TABLE.md/json`

Metrics:

- `paper_count=16`
- `review_negative_verified_count=0`
- `verified_review_issue_count=12`
- `verified_review_issue_cluster_count=8`
- `duplicate_review_issue_row_count=4`
- `reviewer_candidate_review_issue_count=12`
- `reviewer_candidate_review_issue_critique_payload_count=0`
- `reviewer_candidate_review_issue_deterministic_seed_count=12`
- `claim_obligation_review_issue_count=0`
- `verified_missing_ablation_cluster_count=6`
- `mark_contested_commit_count=5`
- `recovery_case_verified_review_issue_repair=5`
- `negative_grounding_conflict_count=0`
- `negative_semantic_anchor_conflict_count=0`
- `semantic_negative_without_review_relation_count=0`
- `negative_evidence_unlinked_to_flaw=0`
- `positive_or_neutral_negative_candidate_count=0`
- protection: PASS

This run is not a full hardneg20 result. It stopped at 16/20 because MiMo returned `402 Insufficient account balance`.

## Code Change Since P28.5

P28.6 cleans final-view hygiene without increasing issue counts:

- Quote-bank generated negative candidates whose evidence is not actually negative are treated as safe rejected anchors, not active negative-grounding conflicts.
- Stale `reviewer_absence_audit` evidence/flaws that no longer pass the current bundle verifier are treated as rejected stale anchors, not active conflicts.
- Ordinary direct negative misbindings still remain active conflicts.

This changed `negative_grounding_conflict_count` and `negative_semantic_anchor_conflict_count` to 0 for both the TargetRefine2 offline recompute and fresh partial16 recompute.

## Remaining Risks

- A fresh full hardneg20 MiMo rerun is blocked by MiMo account balance.
- Most verified review issues are deterministic reviewer seeds, not Critique payload candidates.
- Issue diversity is still missing-ablation heavy.
- Direct quote-grounded reviewer negatives remain zero.
- Live recovery counts from offline recompute should be described carefully; the strongest live rerun evidence is only partial16 until MiMo balance is restored.

## Next Steps

1. Restore MiMo balance or provide another working MiMo key, then rerun full hardneg20 with the current P28.6 code.
2. Manually audit the P28.6 full20 cluster table; carry forward the 8/9 TargetRefine2 A/B judgment only if the cluster set stays identical.
3. Improve candidate diversity by moving more entity-level obligations into claim/inventory extraction rather than relying on deterministic missing-ablation seeds.
4. Keep direct quote-grounded negative evidence strict and separate from obligation-grounded issue bundles.
