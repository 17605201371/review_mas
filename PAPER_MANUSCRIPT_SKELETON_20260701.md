# Manuscript Skeleton

Date: 2026-07-01

This file assembles the current paper narrative into a first manuscript skeleton. It is not a final paper draft. Its job is to keep the story coherent across introduction, related work, method, experiments, figures, limitations, and conclusion while preserving the current P28.6 evidence boundaries.

Primary source drafts:

- `PAPER_INTRODUCTION_DRAFT_20260701.md`
- `PAPER_RELATED_WORK_DRAFT_20260701.md`
- `PAPER_METHOD_SECTION_DRAFT_20260701.md`
- `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`
- `PAPER_FIGURE_SPECS_20260701.md`
- `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md`

## Working Title

Main candidate:

> ReviewState Maintenance for Conservative LLM-Assisted Peer Review

Alternative candidates:

1. ReviewState-Driven Verification for LLM-Assisted Peer Review
2. From Review Generation to ReviewState Maintenance
3. Auditable ReviewState Maintenance for LLM-Assisted Paper Reviewing

Avoid titles that promise broad autonomous flaw discovery or accept/reject prediction.

## Abstract Draft

Large language models can generate plausible peer-review text, but fluent reviews may still lose track of which claims are supported, contested, or merely speculative. We present DrMAS, a ReviewState-driven framework for LLM-assisted peer review that represents claims, evidence, reviewer issues, conflicts, hygiene diagnostics, and recovery actions as structured state. DrMAS separates direct quote-grounded negative evidence from obligation-grounded review issues: the latter can be verified through a claim anchor, observed paper inventory, a concrete missing or mismatched entity, and counterevidence checks, without pretending that the paper itself contains a negative sentence. On a hard-negative diagnostic set, the current P28.6 pipeline verifies 13 obligation-grounded issue rows, deduplicating to 9 issue clusters; manual audit judges 8 of 9 clusters valid or defensible. The direct quote-grounded negative lane remains strict and produces no verified direct negatives, highlighting the difference between copied negative quotes and reviewer-inferred issue bundles. Final-view hygiene remains clean in the authoritative artifacts, with zero active negative-grounding conflicts, zero semantic anchor conflicts, zero unlinked negative evidence, and zero positive/neutral negative candidates. These results support a conservative view of LLM review assistance as auditable state maintenance and repair rather than unconstrained review generation.

Abstract caveats:

- Keep `review_negative_verified_count=0` visible.
- Use `9 issue clusters` and `8/9 manual A/B clusters` as the headline, not `13 defects`.
- Do not claim a fresh full20 rerun until MiMo balance is restored and the run completes.

## 1. Introduction

Source: `PAPER_INTRODUCTION_DRAFT_20260701.md`.

### Intended Flow

1. LLM reviews can be fluent but state-incoherent.
2. Critical review content is especially fragile because direct negative quotes are rare.
3. Real reviewer issues often arise from claim-inventory-obligation mismatches.
4. DrMAS reframes the task as ReviewState maintenance.
5. Contributions: two critical-content lanes, review issue bundle verification, final-view hygiene, non-destructive recovery.
6. Conservative P28.6 result and limitations.

### Drop-In Contribution Paragraph

This paper makes the following contributions. First, we formulate LLM-assisted reviewing as ReviewState maintenance rather than direct review generation, representing claims, evidence, reviewer issues, conflicts, hygiene diagnostics, and recovery actions as structured state. Second, we distinguish direct quote-grounded negative evidence from obligation-grounded review issues, preventing reviewer-inferred absence concerns from being falsely counted as copied paper-negative quotes. Third, we introduce a conservative review issue bundle verifier that checks claim anchors, observed inventory anchors, concrete missing or mismatched entities, counterevidence, and review-worthiness before a concern enters the verified issue view. Fourth, we implement final-view hygiene checks that suppress common false-negative artifacts, including positive or neutral text misused as negative evidence, stale absence records, quote-bank artifacts, retrieval gaps, and unlinked negative evidence. Finally, we show that verified issues can drive non-destructive recovery through contested relations, preserving supported claims while exposing unresolved review concerns.

## 2. Related Work

Source: `PAPER_RELATED_WORK_DRAFT_20260701.md`.

### Section Plan

1. LLM-assisted peer review.
2. Retrieval-augmented and grounded scientific assistance.
3. Factuality, attribution, and evidence verification.
4. Multi-agent reviewing and self-correction.
5. Review-state and argument-state representations.
6. Positioning summary.

### Writing Position

The related-work argument should be:

> Prior work helps models generate, retrieve, ground, verify, critique, or revise text. DrMAS is complementary because it treats review as persistent state maintenance. The contribution is not more agents or looser prompting; it is typed ReviewState objects plus lifecycle verification and non-destructive recovery.

### Citation State

The current related-work draft uses explicit citation placeholders. Before final manuscript use, replace them with verified bibliography entries. Do not invent reference metadata.

## 3. Method

Source: `PAPER_METHOD_SECTION_DRAFT_20260701.md`.

### Section Plan

1. Overview.
2. ReviewState definition.
3. Evidence grounding and claim binding.
4. Two critical-content lanes.
5. Review issue bundle verification.
6. Materializing verified bundles into ReviewState.
7. Final-view hygiene.
8. Recovery as non-destructive repair.
9. Rendering the final review.

### Core Formal Object

Use the existing ReviewState definition:

```text
S = (C, E, F, G, I, K, R, H)
```

where `C` is claims, `E` is evidence, `F` is flaw or concern candidates, `G` is evidence gaps, `I` is verified review issue bundles, `K` is conflict or contested relations, `R` is recovery patches, and `H` is final-view hygiene diagnostics.

### Key Verification Predicate

A candidate bundle should be described as verified only if:

```text
real_claim
AND locatable_claim_anchor
AND concrete_missing_or_mismatch_entity
AND auditable_expectation
AND verifiable_observed_inventory
AND issue_type_relevant_inventory
AND missing_entity_not_already_observed
AND no_ablation_or_full_text_counterevidence
AND review_worthiness_gate
AND not_author_limitation_or_retrieval_gap
```

### Required Figure Placement

- Figure 1: ReviewState lifecycle at the start of Method.
- Figure 2: two critical-content lanes before bundle verification.
- Optional Figure 4: non-destructive recovery near the recovery subsection.

## 4. Experiments

Source: `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`.

### Research Questions

1. Can the system verify reviewer issues without relying on copied negative quotes?
2. Does the final view suppress unsafe negative-evidence artifacts?
3. Can verified issues trigger non-destructive recovery?
4. What still limits the current system?

### Main Setting

Use hardneg20 as a diagnostic set. Main result is P28.6 TargetRefine2 offline recompute:

```text
P28_6_CONFLICTFIX_TARGETREFINE2_194911_*
```

Fresh live evidence is only partial16:

```text
P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*
```

The partial16 run stopped because MiMo returned `402 Insufficient account balance`.

### Main Results Table

Use these P28.6 hardneg20 offline recompute metrics:

| Metric | Value |
| --- | ---: |
| papers | 20 |
| direct quote-grounded reviewer negatives | 0 |
| verified review issue rows | 13 |
| verified review issue clusters | 9 |
| duplicate review issue rows | 4 |
| reviewer-candidate issue rows | 13 |
| critique-payload candidate rows | 2 |
| deterministic-seed candidate rows | 11 |
| claim-obligation fallback rows | 0 |
| verified missing-ablation clusters | 6 |
| mark-contested commits | 14 |
| verified-review-issue repairs | 6 |
| active negative grounding conflicts | 0 |
| semantic anchor conflicts | 0 |
| semantic negatives without review relation | 0 |
| unlinked negative evidence | 0 |
| positive/neutral negative candidates | 0 |
| protection | PASS |

### Manual Audit Table

Use cluster-level quality:

| Cluster target | Issue type | Manual label | Paper use |
| --- | --- | --- | --- |
| recurrent draft model | missing_ablation | A | strong case study |
| acceptance prediction head | missing_ablation | A | strong case study |
| generalized noise regularization | missing_ablation | A | strong case study |
| class-balancing CE loss | missing_ablation | B | defensible example |
| GrCN / ControllNet reproducibility details | reproducibility_gap | B | defensible example |
| PropGCL transformation phase / weights | missing_ablation | B | defensible example |
| recent GNN / graph-transformer baselines | missing_baseline | B | defensible example |
| EqualAL baseline | missing_baseline | B | defensible example |
| number of motion components beyond K=4 | missing_ablation | C | exclude from conservative quality count |

### Required Figure Placement

- Figure 3: row-to-cluster-to-manual-audit funnel before or after the main result table.

## 5. Discussion

### Main Interpretation

The useful critical-review signal in the current system is not copied negative paper text. It is verified claim-inventory-obligation mismatch. This is the central insight that makes the P28.6 result valuable despite `review_negative_verified_count=0`.

### What The Result Supports

The result supports these claims:

- DrMAS can verify obligation-grounded review issue bundles conservatively.
- The final-view hygiene layer can keep measured false-negative-evidence artifacts out of the final view.
- Verified issues can produce non-destructive supported-but-contested relations.
- Row count must be deduplicated into clusters before being used as a paper-facing quality metric.

### What The Result Does Not Support

The result does not support these claims:

- DrMAS finds many direct negative quotes.
- DrMAS broadly discovers diverse reviewer issues autonomously.
- DrMAS improves accept/reject accuracy.
- Recovery fixes review decisions.
- The fresh MiMo run completed full20.

## 6. Limitations

Use these limitations explicitly.

1. Direct quote-grounded negative discovery remains weak: `review_negative_verified_count=0`.
2. Issue type diversity is limited; the current verified clusters are missing-ablation heavy.
3. Critique-driven candidate recall is immature: only 2 verified rows come from Critique payload candidates in the main offline recompute.
4. The freshest MiMo live rerun is partial16 because the MiMo API returned `402 Insufficient account balance`.
5. Hardneg20 is a diagnostic set, not a broad benchmark.
6. Related work references still need verified bibliography entries.

## 7. Conclusion Draft

LLM-assisted peer review should not be evaluated only as a problem of generating fluent review text. A useful review assistant must track what is supported, contested, speculative, stale, or unsafe to render. DrMAS addresses this by maintaining an explicit ReviewState with claims, evidence, review issues, conflicts, hygiene diagnostics, and recovery actions. The current P28.6 results show that obligation-grounded review issues can be verified conservatively through claim anchors, observed inventory, concrete missing or mismatched entities, and counterevidence checks, while measured false-negative-evidence artifacts are kept out of the final view. The direct quote-grounded negative lane remains unsolved in the current run, and broad autonomous issue discovery remains future work. The main contribution is therefore a stateful verification and recovery framework for LLM-assisted reviewing: a way to make review text accountable to an auditable lifecycle before it reaches the final report.

## Tables And Figures Checklist

### Figures

- Figure 1: ReviewState lifecycle.
- Figure 2: two critical-content lanes.
- Figure 3: verification funnel from rows to clusters to manual A/B clusters.
- Optional Figure 4: non-destructive recovery.

### Tables

- Table 1: P28.6 main hardneg20 result.
- Table 2: manual cluster audit.
- Table 3: recovery and safety.
- Table 4: P28 diagnostic progression.

## Current Manuscript Readiness Audit

| Component | Status | Evidence | Remaining Work |
| --- | --- | --- | --- |
| Thesis | Stable | blueprint + intro | keep wording conservative |
| Introduction | Drafted | intro draft | polish after title/venue choice |
| Related work | Drafted with placeholders | related work draft | verify exact bibliography |
| Method | Drafted | method draft | convert implementation anchors into prose if needed |
| Experiments | Drafted | experiment draft + P28.6 artifacts | fresh full20 rerun blocked by MiMo balance |
| Figures | Specified | figure specs | produce final artwork |
| Limitations | Drafted | experiment + skeleton | keep visible in abstract/intro |
| Conclusion | First draft in this skeleton | skeleton | polish after final evidence decision |

## Redline Phrases

Do not use:

- "DrMAS finds many true flaws."
- "DrMAS solves negative evidence discovery."
- "The system finds 13 defects."
- "The model autonomously discovers reviewer issues."
- "Recovery fixes review decisions."
- "The fresh full20 rerun shows ..."

Use instead:

- "DrMAS verifies 9 obligation-grounded review issue clusters."
- "Manual audit judges 8/9 clusters valid or defensible."
- "Direct quote-grounded negative discovery remains weak."
- "Recovery exposes supported-but-contested claims without destructive downgrades."
- "The fresh live rerun is partial16 because MiMo balance was exhausted."
