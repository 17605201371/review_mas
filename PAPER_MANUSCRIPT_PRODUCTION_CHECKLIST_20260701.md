# Paper Manuscript Production Checklist

Date: 2026-07-01

Status: production checklist for turning `PAPER_CONTINUOUS_DRAFT_20260701.md` into a submission-ready manuscript. This is not part of the paper body.

## Current Manuscript State

The continuous draft is aligned with the current P28.6 artifacts and now ends at the paper conclusion instead of carrying a draft-status section in the main text.

The paper-facing result should remain conservative:

- main diagnostic result: 9 obligation-grounded review issue clusters on hardneg20 offline recompute;
- manual quality statement: 8 of 9 clusters are valid or defensible;
- direct quote-grounded negative lane: 0 verified direct negatives;
- fresh live sanity run: partial16 only, stopped by MiMo `402 Insufficient account balance`;
- primary framing: ReviewState maintenance and conservative issue verification, not broad autonomous review generation.

## Remaining Production Tasks

1. Replace draft BibTeX entries with final venue-style BibTeX, using `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md` and `PAPER_REFERENCES_DRAFT_20260701.bib` as the starting point.
2. Render or redraw the Mermaid figure sources into polished SVG/PDF figures.
3. Decide whether to keep hardneg20 as the main experiment or wait for a fresh full20 MiMo rerun.
4. Add an appendix or reproducibility note mapping paper concepts to implementation anchors.
5. Re-audit all result claims after any fresh run changes the dashboard or case tables.

## Submission-Readiness Blockers

- No fresh full20 live rerun is available while MiMo returns `402 Insufficient account balance`.
- Figure sources exist, but final rendered figures are not checked.
- Bibliography keys are internally consistent, but final venue records are not verified.
- The empirical result is diagnostic and small; the paper must not claim broad review-quality improvement.
