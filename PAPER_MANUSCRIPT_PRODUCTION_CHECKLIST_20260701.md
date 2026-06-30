# Paper Manuscript Production Checklist

Date: 2026-07-01

Status: production checklist for turning `PAPER_CONTINUOUS_DRAFT_20260701.md` into a submission-ready manuscript. This is not part of the paper body.

## Current Manuscript State

The continuous draft is aligned with the current P28.6 artifacts and now ends at the paper conclusion instead of carrying a draft-status section in the main text.

Clean paper body draft exists at `PAPER_CLEAN_BODY_DRAFT_20260701.md`. It removes workflow metadata from the continuous draft and uses rendered SVG figure references with paper-facing captions. This is the preferred file for advisor/internal manuscript review.

The implementation/reproducibility appendix draft exists at `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md`; it maps paper concepts to code anchors, scripts, artifacts, and metric checks.

Figure SVG/PDF drafts exist in `paper_figures/`; they were manually redrawn from the Mermaid specs and validated with `rsvg-convert`. They still need target-template placement and final visual QA.

Cleaned draft BibTeX exists at `PAPER_REFERENCES_DRAFT_20260701.bib`, with citation provenance and remaining metadata risks in `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md`.

Empirical framing is recorded in `PAPER_EMPIRICAL_FRAMING_DECISION_20260701.md`: proceed with offline-full20 as the main diagnostic result and partial16 as the live sanity check for the conservative framework draft; require fresh full20 only for stronger benchmark-style claims.

The paper-facing result should remain conservative:

- main diagnostic result: 9 obligation-grounded review issue clusters on hardneg20 offline recompute;
- manual quality statement: 8 of 9 clusters are valid or defensible;
- direct quote-grounded negative lane: 0 verified direct negatives;
- fresh live sanity run: partial16 only, stopped by MiMo `402 Insufficient account balance`;
- primary framing: ReviewState maintenance and conservative issue verification, not broad autonomous review generation.

## Remaining Production Tasks

1. Re-export final venue-style BibTeX records, using `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md`, `PAPER_REFERENCES_DRAFT_20260701.bib`, and `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md` as the starting point.
2. Convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the target venue template.
3. Place the rendered SVG/PDF figures into the target paper template and check scaling, line wrapping, and cropping.
4. Keep the offline-full20/partial16 empirical framing unless MiMo balance is restored and a fresh full20 rerun passes the same checks.
5. Fold the reproducibility appendix into the target paper format after figures and bibliography are finalized.
6. Re-audit all result claims after any fresh run changes the dashboard or case tables.

## Submission-Readiness Blockers

- No fresh full20 live rerun is available while MiMo returns `402 Insufficient account balance`; this blocks broad benchmark-style claims, not the conservative framework draft.
- Figure SVG/PDF drafts exist, but final venue-template placement is not checked.
- Bibliography keys are internally consistent and cleaned, but final target-venue records are not verified.
- The empirical result is diagnostic and small; the paper must not claim broad review-quality improvement.
