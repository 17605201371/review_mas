# Venue Fit Decision

Date: 2026-07-01

Status: paper-positioning decision aid. This is not paper body text and not a venue commitment.

## Current Best Fit

The current DrMAS paper is best positioned as a conservative systems/method or human-AI review-support paper.

The core sell is:

> LLM-assisted peer review should be treated as auditable ReviewState maintenance. DrMAS verifies review-critical state objects, separates direct quote-grounded negatives from obligation-grounded issue bundles, validates the final view, and supports non-destructive contested recovery.

This is a mechanism and state-lifecycle contribution, not a broad benchmark result.

## Venue Families

| Venue family | Fit | Why |
| --- | --- | --- |
| Systems/method venue for LLM applications | Medium-high | The contribution is a concrete ReviewState lifecycle with typed evidence lanes, issue bundles, final-view validation, and recovery actions. |
| Human-AI review-support venue | Medium-high | The paper is honest about limits and frames DrMAS as a conservative assistant rather than an autonomous reviewer. |
| Peer-review automation or scholarly-assistance workshop | High | The diagnostic setting, issue-bundle case study, and state-maintenance framing are directly relevant. |
| Benchmark-heavy ML/NLP main conference | Low-medium | Current empirical evidence is diagnostic: hardneg20, partial live rerun, narrow issue diversity, and direct negatives at 0. |
| General multi-agent LLM venue | Medium | DrMAS uses agents, but the contribution is persistent ReviewState rather than agent orchestration. The paper must avoid being judged as "just another multi-agent workflow." |

## Recommended Submission Path

Preferred path:

1. Advisor/internal review using `PAPER_ADVISOR_REVIEW_PACKET_20260701.md`.
2. Choose between:
   - a systems/method paper about ReviewState maintenance; or
   - a workshop/human-AI review-support paper about conservative reviewer-issue verification.
3. Only after venue direction is chosen, convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the target template.

Do not spend substantial time on a benchmark-heavy venue template until fresh full20 and stronger empirical coverage exist.

## What To Emphasize By Venue

### Systems/Method Framing

Emphasize:

- ReviewState as the central abstraction;
- two critical-content lanes;
- final-view validation;
- non-destructive recovery;
- reproducibility appendix with code anchors and regeneration artifacts.

De-emphasize:

- broad review-generation quality;
- autonomous critique discovery;
- raw issue row count.

### Human-AI Review-Support Framing

Emphasize:

- conservative assistance;
- preventing false negative-evidence artifacts;
- separating verified issues from speculative concerns;
- supported-but-contested claims;
- transparent limitations and manual audit.

De-emphasize:

- accept/reject prediction;
- replacing human reviewers;
- overclaiming issue discovery breadth.

### Peer-Review Automation Workshop Framing

Emphasize:

- why reviewer issues are often not direct negative quotes;
- issue-bundle verification;
- the SpecDec++ case study;
- diagnostic hard-negative evaluation;
- practical failure modes for LLM review systems.

Needed strengthening:

- add more peer-review-specific related work if time allows;
- consider turning the issue-bundle case study into a main-paper table.

### Benchmark-Heavy ML/NLP Framing

Current recommendation: avoid unless new evidence is added.

Would need:

- fresh full20 rerun with current code;
- repeated-seed stability;
- second diagnostic set or oracle/reference-review upper bound;
- broader issue-type diversity;
- clearer autonomous Critique candidate contribution.

## Related Work Implications

The current bibliography is adequate for an internal systems/method draft, but the target venue changes what must be strengthened:

- Systems/method route: current RAG, factuality, multi-agent, and argument-mining references are probably enough for an initial draft, pending final BibTeX export.
- Human-AI or peer-review route: add one or two more LLM peer-review / AI-assisted reviewing references beyond the current Liang et al. citation.
- Benchmark-heavy route: add benchmark and evaluation references, then run more experiments before submission.

Do not invent venue metadata or citations. Use `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md` before adding references.

## Decision Rules

Proceed to template conversion if:

- advisor agrees the paper can be framed as a conservative ReviewState mechanism paper;
- direct quote-grounded negative count 0 remains explicitly visible;
- 9 clusters / 8 A-B clusters remains the headline result;
- hardneg20 is described as diagnostic;
- final-view validation and non-destructive recovery remain central.

Pause template conversion and strengthen experiments if:

- target venue expects broad empirical performance;
- advisor wants autonomous issue discovery claims;
- the direct-negative-zero result is judged unacceptable for the venue;
- manual audit requires a second annotator before review.

## Current Recommendation

Move forward as an internal full-paper draft for advisor review, then choose a systems/method or human-AI review-support venue. The current package is not ready for a benchmark-heavy venue, but it is coherent enough to evaluate as a conservative ReviewState framework paper.
