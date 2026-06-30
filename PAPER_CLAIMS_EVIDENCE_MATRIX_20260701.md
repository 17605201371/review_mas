# Paper Claims And Evidence Matrix

Date: 2026-07-01

Purpose: map every paper-level claim to current evidence, allowed wording, and remaining gaps. This is the guardrail for turning P28.6 artifacts into a manuscript without overstating the result.

## Evidence Sources

Primary current artifacts:

- `PAPER_NARRATIVE_BLUEPRINT_20260701.md`
- `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`
- `P28_6_PAPER_NARRATIVE_STATUS_20260630.md`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`
- `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`
- `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_HARDNEG20_DASHBOARD.md/json`

Current best result is the P28.6 TargetRefine2 offline recompute over hardneg20. The fresh MiMo rerun is only partial16 because MiMo returned `402 Insufficient account balance`.

## Claim Status Legend

- `Supported`: evidence is current and strong enough for paper text.
- `Supported With Caveat`: can be used, but the caveat must appear near the claim.
- `Preliminary`: useful for motivation or future work, not a main result.
- `Blocked`: needs new external state or a fresh run.

## Contribution Claims

| Claim | Status | Evidence | Allowed Wording | Caveat |
| --- | --- | --- | --- | --- |
| DrMAS reframes LLM review as ReviewState maintenance rather than direct review generation. | Supported | ReviewState schema, state/audit/recovery code path, P28.6 narrative docs. | "DrMAS maintains claims, evidence, reviewer issues, conflicts, and recovery actions as auditable state objects." | Do not imply this alone proves better review quality. |
| DrMAS separates direct quote-grounded negative evidence from obligation-grounded review issues. | Supported | P28.6 dashboard: `review_negative_verified_count=0`, `verified_review_issue_cluster_count=9`. | "The system keeps direct paper-negative quotes and obligation-grounded reviewer issues in separate lanes." | Direct negative quote lane currently has zero verified results. |
| DrMAS verifies review issues that are not copied negative quotes. | Supported With Caveat | P28.6 full20: `verified_review_issue_count=13`, `verified_review_issue_cluster_count=9`; manual audit 8/9 A/B. | "The system verifies 9 obligation-grounded issue clusters, 8/9 manually judged valid or defensible." | Use cluster count, not row count. Manual audit is small. |
| DrMAS prevents common false negative-evidence failure modes. | Supported | P28.6: `negative_grounding_conflict_count=0`, `negative_semantic_anchor_conflict_count=0`, `semantic_negative_without_review_relation_count=0`, `positive_or_neutral_negative_candidate_count=0`. | "Final-view hygiene removes active negative-grounding conflicts and positive/neutral negative candidates." | Do not claim no false positives exist globally; this is for measured P28.6 artifacts. |
| DrMAS supports non-destructive recovery through contested relations. | Supported With Caveat | P28.6 full20: `mark_contested_commit_count=14`, `recovery_case_verified_review_issue_repair=6`; partial16: 5/5. | "Verified issues can trigger non-destructive contested repairs." | Full20 recovery numbers are offline recompute over a prior run; fresh rerun is partial16. |
| DrMAS blocks unsafe downgrade behavior. | Supported With Caveat | P28.6 dashboard includes `recovery_unsafe_downgrade_attempt_blocked=1`; tests cover no active conflict leakage. | "Unsafe downgrade attempts are tracked separately and do not become the main recovery story." | Need avoid overstating from one observed blocked attempt. |
| DrMAS discovers diverse reviewer issues. | Preliminary | Current issue set is missing-ablation heavy: `verified_missing_ablation_cluster_count=6` of 9 clusters. | "The current prototype mostly verifies missing-ablation and missing-baseline style issues." | Do not claim broad issue diversity yet. |
| Critique Agent autonomously discovers most issues. | Not Supported | `reviewer_candidate_review_issue_critique_payload_count=2`, `deterministic_seed_count=11`. | Not paper-ready as a positive claim. | Current pipeline relies heavily on deterministic reviewer seeds. |
| DrMAS improves accept/reject accuracy. | Not Supported | The project treats accept/reject as a health check, not a target metric. | Do not claim. | Would require a separate benchmark and evaluation. |

## Experiment Tables To Include

### Table 1: P28.6 Main Hardneg20 Result

Use P28.6 TargetRefine2 offline recompute:

| Metric | Value | Source |
| --- | ---: | --- |
| papers | 20 | dashboard |
| direct quote-grounded reviewer negatives | 0 | dashboard |
| verified issue rows | 13 | dashboard |
| verified issue clusters | 9 | dashboard/case table |
| manual A/B clusters | 8/9 | manual audit |
| verified missing-ablation clusters | 6 | dashboard |
| active negative grounding conflicts | 0 | dashboard |
| semantic anchor conflicts | 0 | dashboard |
| semantic negatives without review relation | 0 | dashboard |
| unlinked negative evidence | 0 | dashboard |
| positive/neutral negative candidates | 0 | dashboard |
| protection | PASS | dashboard |

Caption draft:

> P28.6 verifies obligation-grounded review issue bundles conservatively. The headline is cluster count plus manual audit, not raw row count. Direct quote-grounded negative evidence remains zero.

### Table 2: Issue Cluster Manual Audit

Use the 9 representative clusters:

| Cluster | Type | Manual Label | Paper Use |
| --- | --- | --- | --- |
| recurrent draft model | missing_ablation | A | strong case study |
| acceptance prediction head | missing_ablation | A | strong case study |
| generalized noise regularization | missing_ablation | A | strong case study |
| class-balancing CE loss | missing_ablation | B | defensible example |
| GrCN / ControllNet reproducibility details | reproducibility_gap | B | defensible example |
| PropGCL transformation phase / weights | missing_ablation | B | defensible example |
| recent GNN / graph-transformer baselines | missing_baseline | B | defensible example |
| EqualAL baseline | missing_baseline | B | defensible example |
| number of motion components beyond K=4 | missing_ablation | C | do not count in paper-ready precision claim |

Caption draft:

> Manual audit distinguishes system-verified clusters from paper-ready review-worthy clusters. We report 8/9 A/B clusters as the conservative quality count.

### Table 3: Recovery And Safety

| Metric | Full20 Offline | Fresh Partial16 | Interpretation |
| --- | ---: | ---: | --- |
| mark-contested commits | 14 | 5 | non-destructive contested repair signal |
| verified-review-issue repairs | 6 | 5 | conservative recovery count |
| unsafe downgrade blocked | 1 | not headline | safety diagnostic |
| active negative grounding conflicts | 0 | 0 | hygiene protection |
| unlinked negative evidence | 0 | 0 | linkage protection |

Caption draft:

> Recovery is reported as state repair, not decision correction. Supported claims can remain supported while being contested by verified review issues.

### Table 4: What P28.6 Changed

| Stage | Effect | Evidence |
| --- | --- | --- |
| Raw P28.5 | higher row count but generic/malformed missing-ablation targets | P28.5 raw artifacts |
| TargetRefine2 | removes generic targets, keeps 9 clusters | TargetRefine2 manual audit |
| ConflictFix P28.6 | removes stale/quote-bank false negative anchors from active conflicts | P28.6 conflict metrics all 0 |

Caption draft:

> P28.6 is a precision and hygiene checkpoint, not a recall-boosting step.

## Figure Ideas

### Figure 1: ReviewState Lifecycle

Flow:

```text
Paper -> Claim extraction -> Evidence/inventory -> Review issue bundle verification
      -> Final-view hygiene -> Contested relation / recovery -> Final report
```

Message: final review is generated from audited state, not directly from paper text.

### Figure 2: Two Negative Lanes

```text
Direct quote-grounded negative lane
  copied paper quote -> semantic/review relation verifier -> verified direct negative

Obligation-grounded issue lane
  claim anchor + observed inventory + missing entity + no counterevidence -> verified review issue bundle
```

Message: many real reviewer issues are not copied negative quotes.

### Figure 3: Funnel

Rows -> clusters -> manual A/B clusters:

```text
13 verifier-passing rows -> 9 clusters -> 8 A/B clusters
```

Message: row counts are not the paper headline.

## Required Textual Caveats

Use these caveats explicitly:

- "The direct quote-grounded negative lane remains strict and produced no verified direct negatives in the current run."
- "The main result is obligation-grounded issue verification, not autonomous broad defect discovery."
- "The full20 P28.6 result is an offline recompute over a completed run; the fresh rerun is partial16 because MiMo balance was exhausted."
- "Most current verified issues come from deterministic seeds, so improving Critique-driven candidate recall remains future work."
- "The current issue distribution is missing-ablation heavy."

## Forbidden Phrases

Avoid:

- "DrMAS discovers many true flaws."
- "DrMAS restores negative evidence discovery."
- "The system finds 13 defects."
- "Direct negative evidence is solved."
- "The model autonomously identifies review issues."
- "Recovery fixes wrong decisions."

Prefer:

- "DrMAS verifies 9 obligation-grounded review issue clusters."
- "Manual audit judges 8/9 clusters valid or defensible."
- "Direct quote-grounded negative discovery remains weak."
- "Recovery exposes supported-but-contested claims without destructive downgrades."
- "P28.6 is a precision and hygiene checkpoint."

## Current Blocking Items

1. Fresh full20 P28.6 rerun is blocked by MiMo account balance.
2. Critique-driven candidate recall is still weak.
3. Issue type diversity is too narrow.
4. Hardneg20 is diagnostic, not enough for final broad benchmark claims.

## Next Writing Task

The next document to draft should be either:

1. `PAPER_METHOD_SECTION_DRAFT_20260701.md`: method prose with equations/definitions for ReviewState, issue bundle verification, and recovery;
2. `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`: table-ready experiment narrative and captions using the metrics above.

The experiment section should come first if MiMo balance remains blocked, because it clarifies exactly what additional run would prove.
