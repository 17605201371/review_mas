# Advisor One-Page Brief

Date: 2026-07-01

Status: compact advisor-facing decision brief for the current DrMAS paper narrative. This is not paper body text.

## Decision Needed

Should we proceed with DrMAS as a conservative ReviewState framework paper, rather than waiting for stronger benchmark-style evidence?

My current recommendation is yes for an internal/advisor draft and likely for a systems/method, human-AI review-support, or peer-review automation workshop route. I would not target a benchmark-heavy ML/NLP venue without a fresh full20 rerun, repeated-seed stability, and broader issue diversity.

## One-Sentence Thesis

Reliable LLM-assisted peer review should be treated as auditable ReviewState maintenance: claims, evidence, reviewer issues, conflicts, final-view validation, and recovery actions must be represented as typed state before review text is rendered.

## What Is New

DrMAS is not positioned as a better free-form review generator or accept/reject classifier. The contribution is a review-specific state lifecycle:

- separate direct quote-grounded reviewer negatives from obligation-grounded review issues;
- verify reviewer-inferred issues through claim anchors, observed inventory, concrete missing or mismatched entities, and counterevidence checks;
- keep unsafe negative-evidence artifacts out of the final view;
- use non-destructive `mark_contested` recovery so supported claims can remain supported while unresolved review issues stay visible;
- render final review text from audited state rather than raw model prose.

## Current Evidence

The main paper result is a conservative hardneg20 diagnostic result, not a broad benchmark claim.

| Item | Current Evidence |
| --- | --- |
| Main setting | 20-paper hard-negative diagnostic set |
| Direct quote-grounded reviewer negatives | 0 |
| Verified obligation-grounded issue rows | 13 |
| Deduplicated verified issue clusters | 9 |
| Manual audit | 8 of 9 clusters valid or defensible |
| Issue distribution | 6 missing-ablation, 2 missing-baseline, 1 reproducibility cluster |
| Candidate source caveat | 2 Critique-payload rows, 11 deterministic-seed rows |
| Safety/protection | active negative-grounding conflicts, semantic anchor conflicts, unlinked negative evidence, and positive/neutral negative candidates are all 0 |
| Recovery | 14 full20 mark-contested commits; 6 verified-review-issue repairs |
| Fresh live sanity check | partial16 only; 8 clusters and clean protection lines before MiMo balance stopped the run |

## Mandatory Caveats

- Direct quote-grounded negative discovery remains unsolved in the current result.
- The main full20 result is an offline recompute over a completed MiMo run.
- The freshest live rerun is partial16, not full20.
- Issue diversity is narrow and missing-ablation heavy.
- Autonomous Critique discovery is immature; deterministic reviewer seeds dominate.
- Manual audit is a sanity check over 9 clusters, not a population precision estimate.
- DrMAS is review support and audit infrastructure, not an autonomous reviewer, accept/reject system, or source of final review judgments.

## Advisor Questions

1. Is the ReviewState-maintenance thesis strong enough for the intended venue family?
2. Should the paper foreground obligation-grounded issue bundles as the main conceptual novelty, or make them one mechanism inside the broader ReviewState lifecycle?
3. Is it acceptable to keep the zero direct-negative result visible in the abstract, or should it move to experiments/limitations?
4. Does the compact SpecDec++ issue-bundle table belong in the main paper, or should it move to appendix under venue space limits?
5. Is a second annotator required before submission, or is the 8/9 cluster audit acceptable as a transparent sanity check?
6. Should we spend the next effort on venue-template production, or on fresh full20 / repeated-seed / second-diagnostic-set evidence?

## Recommended Next Step

Use `PAPER_CLEAN_BODY_DRAFT_20260701.md` as the manuscript body and this brief as the advisor entry point. If the advisor accepts the conservative framework framing, choose the venue family first, then move to template conversion, final BibTeX export, figure placement QA, and appendix integration. If the advisor wants benchmark-style claims, pause template work and strengthen experiments first.
