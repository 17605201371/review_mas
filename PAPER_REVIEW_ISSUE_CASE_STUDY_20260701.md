# Review Issue Bundle Case Study

Date: 2026-07-01

Status: paper-support appendix for explaining one verified obligation-grounded issue bundle. This is not a new experiment.

## Purpose

The main manuscript argues that many real reviewer issues are not direct negative quotes. This case study shows the mechanism on one authoritative P28.6 cluster:

- source case table: `P28_6_CONFLICTFIX_TARGETREFINE2_194911_REVIEW_ISSUE_CASE_TABLE.md/json`;
- source recovery table: `P28_6_CONFLICTFIX_TARGETREFINE2_194911_RECOVERY_CASE_TABLE.md/json`;
- paper id: `NnExMNiTHw`;
- cluster target: `acceptance_prediction_head`;
- issue type: `missing_ablation`;
- manual audit class: A, listed as a strong case study in the paper-facing manual audit table.

## Bundle Components

| Bundle field | Value |
| --- | --- |
| Claim anchor | "SpecDec++ introduces an adaptive candidate length mechanism to boost speculative decoding performance, replacing a fixed hyperparameter K." |
| Observed inventory anchor | "We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens." |
| Missing or mismatched item | component-isolation ablation for the acceptance prediction head |
| Inventory count | 2 |
| Inventory sources | reviewer-candidate observed inventory; component anchor for missing ablation |
| Target quality | high |
| Target-quality reason | named or mechanistic missing-ablation target |
| Verification basis | claim anchor is locatable and the auditable expectation has verified inventory |
| Cluster size | 3 rows over claim-1, claim-2, and claim-3 |

## Why This Is Not A Direct Negative Quote

The observed inventory quote is positive or neutral paper content. It says the paper uses a trained acceptance prediction head. It does not say the paper is flawed, underperforming, or invalid.

The verified issue is therefore not:

```text
paper quote directly states a negative result
```

It is:

```text
paper makes a claim about an adaptive candidate-length mechanism
AND paper inventory shows a named acceptance prediction head
AND the issue target is a concrete paper-specific mechanism
AND the verified inventory does not show a component-isolation ablation for that mechanism
AND the target-quality gate classifies the target as high confidence
```

This is the paper's central distinction. The inventory quote is evidence that the mechanism exists; the reviewer issue comes from the missing relation between the claim, the mechanism, and the expected ablation.

## Recovery Behavior

The recovery table records a non-destructive repair for the same paper:

| Field | Value |
| --- | --- |
| turn | 4 |
| bucket | verified_review_issue_repair |
| operation | mark_contested |
| target | claim-1 |
| status transition | supported -> supported |
| evidence bucket | obligation_grounded_review_issue |
| negative type | missing_ablation |

This is the intended recovery story. The claim remains supported, but the state records that it is contested by a verified review issue. The system does not need to downgrade the claim or treat the neutral inventory quote as direct negative evidence.

## Paper-Facing Interpretation

This case is useful because it shows all four pieces of the ReviewState argument:

1. The support lane remains intact: the paper has method evidence for the adaptive candidate-length mechanism.
2. The issue lane is separate: the missing ablation is verified as an obligation-grounded issue, not as direct quote-grounded negative evidence.
3. The target is concrete: the acceptance prediction head is a named mechanism, not a generic "component" placeholder.
4. Recovery is non-destructive: the system marks the supported claim as contested rather than rewriting it as unsupported.

Recommended main-text wording:

> In an illustrative SpecDec++ case, DrMAS treats the paper's statement that it uses a trained acceptance prediction head as neutral inventory evidence. The verified issue is not that the quote is negative; it is that the named mechanism supports a claim about adaptive candidate length while the verified inventory does not show a component-isolation ablation for the head. Recovery therefore marks the supported claim as contested instead of downgrading the claim.

## Caveats

- This is one case study, not a statistical result.
- The candidate source is deterministic reviewer seeding, so it should not be used to claim mature autonomous Critique discovery.
- The row cluster has three related rows; the paper should discuss it as one issue cluster, not three independent defects.
- The case supports the ReviewState lifecycle narrative, not a broad claim that DrMAS finds many flaws.
