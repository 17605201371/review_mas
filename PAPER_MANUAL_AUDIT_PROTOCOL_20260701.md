# Manual Audit Protocol

Date: 2026-07-01

Status: paper-support protocol for the cluster-level manual audit. This is not a new experiment and not a population-level precision estimate.

## Purpose

The paper reports that the authoritative full20 diagnostic result contains 9 verified obligation-grounded review issue clusters, with 8 of 9 manually judged valid or defensible. This protocol makes the manual label meaning explicit so the paper does not rely on an undefined "A/B" shorthand.

Source audit:

- `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`

Source system artifacts:

- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`
- `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`

The P28.6 artifacts are the authoritative reported metrics. The TargetRefine2 manual audit supplies the cluster-level human judgment over the same retained issue-cluster family after precision guards.

## Audit Unit

The audit unit is a deduplicated review issue cluster, not a raw issue row.

This matters because one real issue can appear in multiple rows when overlapping claims point to the same missing or mismatched target. For example, the SpecDec++ acceptance-prediction-head issue appears in three rows but is counted as one cluster.

## Evidence Available To The Auditor

For each cluster, the auditor checks:

1. paper identifier;
2. issue type;
3. normalized cluster target;
4. claim anchor;
5. observed inventory anchor;
6. missing or mismatched entity;
7. verifier target-quality signal when applicable;
8. known counterevidence or caveats in the available paper text;
9. whether the cluster is a duplicate row family or one independent issue.

The auditor does not treat model prose alone as evidence. A cluster is review-worthy only when the claim/inventory/missing-entity relation remains plausible after inspecting the system case table and available caveats.

## Labels

| Label | Meaning | Paper use |
| --- | --- | --- |
| A | Clear review-worthy issue. The claim, inventory, and missing/mismatch relation are specific and central enough that the concern is strong under the available paper text. | Strong example or case-study candidate. |
| B | Defensible reviewer concern. The target is concrete and the concern is useful, but wording should stay cautious because the issue may be less central, broader, or partly dependent on available-text coverage. | Counted in the conservative A/B quality statement, not as a decisive flaw. |
| C | Plausible but too strict, over-demanding, or template-like for the paper-ready headline. | Excluded from conservative A/B count; may be discussed as a caution. |
| D | False positive. The cluster is contradicted by available evidence, generic, off-claim, or not review-worthy. | Excluded; should trigger verifier or target-quality improvement. |

## Current Labels

| Cluster target | Issue type | Label | Rationale |
| --- | --- | --- | --- |
| recurrent draft model | missing_ablation | A | Core ReDrafter mechanism; missing isolation is a strong reviewer issue. |
| acceptance prediction head | missing_ablation | A | Core SpecDec++ mechanism; count once despite three related rows. |
| generalized noise regularization | missing_ablation | A | Named contribution mechanism; strong missing-ablation issue. |
| class-balancing cross-entropy loss | missing_ablation | B | Specific training/loss mechanism; defensible if no isolated ablation covers it. |
| GrCN / ControllNet reproducibility details | reproducibility_gap | B | Concrete reproducibility concern, but not a decisive reject flaw by itself. |
| PropGCL transformation phase / weights | missing_ablation | B | Specific mechanism/efficiency issue; wording should stay cautious. |
| recent GNN / graph-transformer baselines | missing_baseline | B | Defensible baseline-family concern, but broader than a named missing method. |
| EqualAL baseline | missing_baseline | B | Paper-named comparator concern in same-setting active learning. |
| number of motion components beyond K=4 | missing_ablation | C | Plausible but too demanding because available evidence already includes K sensitivity up to K=4. |

Current conservative quality statement:

```text
9 system-verified issue clusters; 8/9 manually judged A or B.
```

Current stronger case-study statement:

```text
3 clusters are A-class strong examples.
```

## Reporting Rules

Allowed:

- "manual audit judges 8 of 9 clusters valid or defensible";
- "manual audit is a sanity check on the cluster-level result";
- "A/B clusters are review-worthy under the available paper text";
- "the C-class cluster is excluded from the conservative quality count."

Not allowed:

- "manual precision is 88.9%";
- "DrMAS finds 8 true defects";
- "A/B clusters are independent reject-level flaws";
- "the manual audit establishes broad review-quality performance";
- "the raw 13 rows are 13 independent defects."

## Limitations

- The audit is small and single-pass.
- There is no independent second annotator yet.
- Labels are based on available paper text and current artifacts.
- The audit supports conservative narrative quality control, not population-level statistical claims.

## Next Strengthening Step

If the paper moves toward a stronger empirical claim, add:

1. a second annotator;
2. adjudication rules for A/B/C/D disagreements;
3. a compact case appendix for all 9 clusters;
4. repeated-run stability if fresh API access becomes available.
