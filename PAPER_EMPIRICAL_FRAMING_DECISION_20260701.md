# Paper Empirical Framing Decision

Date: 2026-07-01

Status: narrative decision memo. This file resolves the current evidence-framing question for the DrMAS paper draft: whether the paper should wait for a fresh full20 MiMo run before the main story can proceed.

## Decision

Use the completed P28.6 offline full20 recompute as the main diagnostic result for the current paper draft, and use the fresh MiMo partial16 run only as a live-run sanity check.

Do not block the paper narrative on a fresh full20 rerun while MiMo returns `402 Insufficient account balance`.

This decision is valid only for a conservative framework/mechanism paper. It is not valid for a broad benchmark-performance claim.

## Rationale

The paper's central claim is not that DrMAS broadly improves review quality or autonomously discovers many defects. The central claim is that LLM-assisted reviewing should be treated as auditable ReviewState maintenance, with separate lanes for direct quote-grounded negatives and obligation-grounded review issues.

The current artifacts are sufficient to support that mechanism-level claim:

- the full20 offline recompute applies the current verifier and final-view hygiene to a completed hardneg20 run;
- the main result is cluster-level and conservative: 13 rows, 9 clusters, 8/9 manual A/B;
- direct quote-grounded negatives remain 0 and are explicitly framed as a limitation;
- final-view hygiene metrics are 0 for the measured conflict/protection lines;
- the fresh partial16 live rerun is directionally consistent but incomplete because of account balance.

Waiting for fresh full20 would improve empirical confidence, but it should not stop the paper narrative package from reaching advisor/internal-review quality.

## Main Evidence To Cite

Use these as the authoritative result artifacts:

- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`
- `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`

Use these only as a partial live-run sanity check:

- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*`

## Allowed Paper Wording

Use:

> On a hardneg20 diagnostic set, the current DrMAS pipeline verifies 13 obligation-grounded issue rows that deduplicate to 9 issue clusters. Manual audit judges 8 of the 9 clusters valid or defensible. A fresh live MiMo rerun completed 16 of 20 papers before account balance exhaustion and showed consistent protection behavior, so we treat it as a sanity check rather than the main full20 result.

Use:

> We report the full20 result as an offline recompute with the current verifier and final-view hygiene, not as a fresh live rerun.

Use:

> These results support a conservative ReviewState-maintenance claim, not a broad benchmark-performance claim.

## Disallowed Paper Wording

Do not write:

- "A fresh full20 rerun confirms the result."
- "DrMAS discovers many true review flaws."
- "DrMAS solves negative evidence discovery."
- "DrMAS improves review quality broadly."
- "The partial16 run is equivalent to a completed full20 run."
- "The 13 issue rows are 13 independent defects."

## How This Changes The Current Draft

The continuous manuscript should not say that a fresh full20 run is required before the current results can be treated as paper evidence. That is too strong for the conservative framework narrative.

Better:

> A fresh full20 rerun would be needed for stronger stability and benchmark-style claims. For the current framework paper, we report the full20 offline recompute as the main diagnostic result and the partial16 live rerun as a sanity check.

## Remaining Empirical Work

Fresh full20 is still valuable if MiMo balance/key is restored:

1. run fresh full20 with current code and flags;
2. regenerate dashboard, review issue table, and recovery table;
3. re-audit all result claims;
4. replace the offline-full20 framing if the fresh run passes the same protection and quality checks.

Until then, the paper should proceed with a conservative offline-full20/partial16 framing.
