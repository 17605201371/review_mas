# Paper Narrative Blueprint

Date: 2026-07-01

This file turns the current P28.6 state into a paper-facing narrative. It is intentionally stricter than a development log: every claim below is either currently supported by artifacts, explicitly marked as a limitation, or listed as a required next experiment.

Companion guardrail: `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md` maps each paper-level claim to current artifacts, allowed wording, table-ready metrics, and forbidden overclaims.

Introduction prose draft: `PAPER_INTRODUCTION_DRAFT_20260701.md`.

Experiment prose draft: `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md`.

Method prose draft: `PAPER_METHOD_SECTION_DRAFT_20260701.md`.

Related work draft: `PAPER_RELATED_WORK_DRAFT_20260701.md`.

Bibliography candidates: `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md`.

Draft BibTeX: `PAPER_REFERENCES_DRAFT_20260701.bib`.

Figure specs: `PAPER_FIGURE_SPECS_20260701.md`.

Renderable figure draft: `PAPER_FIGURES_DRAFT_20260701.md` plus `paper_figures/*.mmd`.

Manuscript skeleton: `PAPER_MANUSCRIPT_SKELETON_20260701.md`.

Continuous manuscript draft: `PAPER_CONTINUOUS_DRAFT_20260701.md`.

Submission readiness audit: `PAPER_READINESS_AUDIT_20260701.md`.

## 1. Thesis

The paper should not claim that DrMAS is a better free-form review generator or a better accept/reject classifier.

The defensible thesis is:

> LLM-assisted paper review needs an explicit, auditable ReviewState. DrMAS represents claims, evidence, reviewer issues, conflicts, and recovery actions as structured state objects, then verifies and repairs that state before producing the final review.

The key shift is from "generate a review" to "maintain and audit a review state."

## 2. Core Insight

True review defects are often not copied negative quotes from the paper. Many useful reviewer concerns are obligation-grounded mismatches:

- a claim requires an ablation, but the observed inventory does not isolate the claimed component;
- a comparison claim omits a relevant baseline family;
- a method claim lacks enough implementation detail for reproduction;
- a supported claim should remain supported but be marked contested by a verified reviewer issue.

Therefore, DrMAS keeps two lanes separate:

- `review_negative_verified_count`: direct quote-grounded paper-negative evidence. This remains strict and currently stays at 0.
- `verified_review_issue_count` / `verified_review_issue_cluster_count`: obligation-grounded review issue bundles. This is the current main result.

This separation is important. It prevents the system from treating author limitations, positive metric statements, quote-bank artifacts, or retrieval gaps as real reviewer negatives.

## 3. Method Story

The method should be explained as a lifecycle, not as a single prompt.

### Stage A: Structured ReviewState

DrMAS constructs a ReviewState with:

- paper claims;
- evidence records with grounding and semantic labels;
- flaw or concern candidates;
- review issue bundles;
- contested relations;
- recovery patch logs;
- final-view hygiene diagnostics.

Paper message: the state gives the reviewer output a traceable substrate.

### Stage B: Evidence And Inventory

Positive evidence is not just a quote list. It is bound to claims and later used to decide whether claims are supported, contested, or under-covered.

Evaluation/method inventory is treated as positive or neutral paper content. It can anchor absence-style reviewer issues without pretending the paper contains a negative sentence.

### Stage C: Review Issue Bundles

A verified review issue bundle requires:

- a real paper claim;
- a locatable claim anchor;
- a concrete missing or mismatched entity;
- observed paper inventory with a locatable quote/table/list anchor;
- no current counterevidence that resolves the issue;
- no author self-limitation, retrieval gap, generic gap, or quote-bank artifact.

This is the most important current contribution. It is how DrMAS verifies issues like missing ablations and missing baselines without fabricating quote-grounded negatives.

### Stage D: Final-View Hygiene

The final view filters or downgrades unsafe artifacts:

- non-real support;
- unlinked negative evidence;
- positive/neutral text misused as negative;
- stale reviewer-absence audit artifacts;
- quote-bank negative candidates that are not actually negative;
- semantic negative anchors without a verified review relation.

P28.6 specifically cleaned the last two categories so they no longer appear as active negative-grounding conflicts.

### Stage E: Recovery

Recovery should be framed as non-destructive state repair:

- preferred action: `mark_contested`;
- supported claims are preserved;
- verified issues can contest a claim without downgrading claim status;
- unsafe downgrade attempts are blocked or counted separately.

The paper should not overclaim recovery as "fixing the paper's decision." It exposes and repairs state inconsistencies.

## 4. Current Evidence

### Main Offline Hardneg20 Result

Authoritative artifact: `P28_6_CONFLICTFIX_TARGETREFINE2_194911_*`.

Current metrics:

| Metric | Value |
| --- | ---: |
| papers | 20 |
| direct quote-grounded reviewer negatives | 0 |
| verified review issue rows | 13 |
| verified review issue clusters | 9 |
| duplicate rows | 4 |
| reviewer-candidate issue rows | 13 |
| critique-payload candidate rows | 2 |
| deterministic-seed candidate rows | 11 |
| claim-obligation fallback rows | 0 |
| verified missing-ablation clusters | 6 |
| mark-contested commits | 14 |
| verified-review-issue recovery repairs | 6 |
| negative grounding conflicts | 0 |
| semantic anchor conflicts | 0 |
| semantic negatives without review relation | 0 |
| unlinked negative evidence | 0 |
| positive/neutral negative candidates | 0 |
| protection | PASS |

Manual audit from `P28_5_TARGETREFINE2_MANUAL_CLUSTER_AUDIT_20260630.md`:

- system clusters: 9;
- manual A/B clusters: 8/9;
- strong A clusters: recurrent draft model, acceptance prediction head, generalized noise regularization;
- one C cluster: `number_motion_components_beyond`.

Paper-facing result:

> On hardneg20, DrMAS produced 9 verified obligation-grounded review issue clusters; manual audit judged 8/9 as valid or defensible. The system maintained zero active negative-grounding conflicts and zero unlinked negative evidence.

### Fresh MiMo Partial Rerun

Authoritative artifact: `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*`.

This is useful but incomplete:

| Metric | Value |
| --- | ---: |
| papers completed | 16/20 |
| verified review issue rows | 12 |
| verified review issue clusters | 8 |
| direct quote-grounded reviewer negatives | 0 |
| mark-contested commits | 5 |
| verified-review-issue recovery repairs | 5 |
| active negative grounding conflicts | 0 |
| protection | PASS |

The run stopped because MiMo returned `402 Insufficient account balance`. Do not present it as a full hardneg20 rerun.

## 5. Claims The Paper Can Make Now

1. DrMAS separates direct quote-grounded negative evidence from obligation-grounded reviewer issues.
2. DrMAS can verify review issues that are not copied negative quotes, using claim anchors, observed inventory, concrete missing entities, and counterevidence checks.
3. P28.6 shows a conservative hardneg20 result: 9 system issue clusters, 8/9 manually judged A/B, with protection lines passing.
4. Non-destructive recovery works in the current pipeline: verified issues can lead to contested relations without downgrading supported claims.
5. Final-view hygiene is measurable: active negative-grounding conflicts, semantic anchor conflicts, unlinked negative evidence, and positive/neutral negative candidates are all 0 in P28.6 artifacts.

## 6. Claims The Paper Should Not Make Yet

1. Do not claim DrMAS finds many direct negative quotes. `review_negative_verified_count=0`.
2. Do not claim broad issue diversity. The current verified issues are missing-ablation heavy.
3. Do not claim Critique Agent alone discovers most issues. Most current verified issues are deterministic reviewer seeds.
4. Do not claim a fresh full20 P28.6 rerun. MiMo stopped at 16/20.
5. Do not use row count as the headline. Use cluster count and manual A/B cluster count.
6. Do not claim accept/reject accuracy as the contribution.

## 7. Suggested Paper Structure

### Introduction

Draft artifact: `PAPER_INTRODUCTION_DRAFT_20260701.md`.

Problem: LLM review generation can sound plausible while losing track of what is actually supported, contested, or speculative.

Gap: Existing review-generation pipelines lack persistent state, lifecycle checks, and recovery mechanisms for evidence and reviewer issues.

Thesis: DrMAS turns review generation into ReviewState maintenance.

Key contribution sentence:

> We introduce a ReviewState-driven review assistant that explicitly represents claims, evidence, reviewer issues, conflicts, and repair actions, enabling conservative verification of obligation-grounded review issues that are not directly expressed as negative paper quotes.

### Related Work

Draft artifact: `PAPER_RELATED_WORK_DRAFT_20260701.md`.

Position against:

- generic LLM review generation;
- retrieval-augmented reviewing;
- factuality/grounding verification;
- agentic self-correction.

Differentiator: DrMAS is not only grounded generation; it is state lifecycle management with verified issue bundles and recovery patches.

### Method

Recommended subsections:

1. ReviewState schema;
2. evidence grounding and claim binding;
3. obligation-grounded review issue bundle verification;
4. final-view hygiene;
5. recovery patches and contested relations.

### Experiments

Recommended tables:

1. Protection/hygiene table: all redlines and P28.6 values.
2. Review issue result table: rows, clusters, manual A/B clusters, issue type distribution.
3. Recovery table: mark-contested commits, verified-review-issue repairs, unsafe downgrade blocked.
4. Case study table: 3 strong A clusters plus 2 defensible B clusters.
5. Ablation/diagnostic table: older raw count vs TargetRefine2 vs P28.6 conflict fix.

### Discussion

The paper should explicitly discuss why direct negative quote count is 0 and why that is not a failure of the main thesis. The important issue is that real review concerns often come from claim/inventory mismatch rather than paper-authored negative sentences.

### Limitations

Current limitations:

- direct quote-grounded negative discovery remains weak;
- candidate diversity is limited;
- many candidates come from deterministic seeds;
- full P28.6 MiMo rerun is blocked by account balance;
- manual audit is still needed to claim A/B quality;
- hardneg20 is a small diagnostic set, not a final benchmark.

## 8. Next Experiments Needed For Paper-Ready Status

### Required

1. Restore MiMo balance or provide a working MiMo key.
2. Run fresh full hardneg20 with current P28.6 code.
3. Regenerate dashboard, review issue case table, and recovery table.
4. Manually audit the resulting clusters.
5. Confirm:
   - `verified_review_issue_cluster_count >= 8`;
   - manual A/B clusters >= 7;
   - active conflict metrics remain 0;
   - `negative_evidence_unlinked_to_flaw=0`;
   - `positive_or_neutral_negative_candidate_count=0`.

### High Value But Not Mandatory For First Draft

1. Follow `PAPER_READINESS_AUDIT_20260701.md`: polish the continuous draft, render figures, finalize bibliography, and choose the empirical path.
2. Polish `PAPER_CONTINUOUS_DRAFT_20260701.md` into a venue-ready manuscript draft.
3. Render or redraw the Mermaid figure sources into polished paper figures.
4. Replace draft BibTeX entries with final venue-style records, using `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md` and `PAPER_REFERENCES_DRAFT_20260701.bib` as the starting point.
5. Improve Critique payload candidate recall so fewer verified issues come from deterministic seeds.
6. Increase issue type diversity beyond missing ablation.
7. Add a small oracle/reference-review analysis as an upper-bound evaluation, not as system input.
8. Run a repeated-seed stability check if budget permits.

## 9. Current One-Paragraph Abstract Draft

Large language models can generate plausible paper reviews, but their conclusions often lack a persistent, auditable account of which claims are supported, contested, or merely speculative. We present DrMAS, a ReviewState-driven framework for LLM-assisted peer review that explicitly maintains claims, evidence, reviewer issues, conflicts, and recovery actions. DrMAS separates direct quote-grounded negative evidence from obligation-grounded review issues, allowing the system to verify concerns such as missing ablations or missing baselines through claim anchors, observed paper inventory, concrete missing entities, and counterevidence checks. On a hard-negative diagnostic set, the current system verifies 9 obligation-grounded review issue clusters, 8 of which are judged valid or defensible by manual audit, while maintaining zero active negative-grounding conflicts and zero unlinked negative evidence. These results support a conservative view of LLM review assistance as auditable state maintenance rather than unconstrained review generation.

## 10. Current Status In One Sentence

P28.6 is good enough to support the paper's ReviewState and verified-review-issue narrative, but not enough to claim broad autonomous defect discovery; the next bottleneck is a fresh full20 rerun plus improved Critique-driven issue diversity.
