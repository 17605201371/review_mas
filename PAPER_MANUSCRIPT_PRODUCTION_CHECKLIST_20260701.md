# Paper Manuscript Production Checklist

Date: 2026-07-01

Status: production checklist for turning `PAPER_CONTINUOUS_DRAFT_20260701.md` into a submission-ready manuscript. This is not part of the paper body.

## Current Manuscript State

The continuous draft is aligned with the current P28.6 artifacts and now ends at the paper conclusion instead of carrying a draft-status section in the main text.

Clean paper body draft exists at `PAPER_CLEAN_BODY_DRAFT_20260701.md`. It removes workflow metadata from the continuous draft and uses rendered SVG figure references with paper-facing captions. It has also been polished to keep engineering run identifiers and API failure details out of the main experimental narrative. This is the preferred file for advisor/internal manuscript review.

Advisor review packet exists at `PAPER_ADVISOR_REVIEW_PACKET_20260701.md`. It lists the small set of files to read first, the current thesis, the defensible empirical claim, mandatory caveats, and concrete questions for advisor review.

Reviewer pre-mortem exists at `PAPER_REVIEWER_PREMORTEM_20260701.md`. It translates the current risk profile into likely reviewer objections, honest responses, forbidden responses, and concrete manuscript actions.

Issue-bundle case study exists at `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md`. It expands the SpecDec++ acceptance-prediction-head cluster into claim anchor, observed inventory anchor, missing entity, target-quality gate, and non-destructive recovery behavior. The clean body now includes a short illustrative case subsection that points to this appendix.

Manual audit protocol exists at `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md`. It defines A/B/C/D cluster labels, reporting rules, and non-claims for the 8/9 manual quality statement. The clean body now gives the short A/B/C definition in the manual-cluster-audit section.

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
4. Use `PAPER_ADVISOR_REVIEW_PACKET_20260701.md` for advisor/internal review before doing heavy venue-template work.
5. Use `PAPER_REVIEWER_PREMORTEM_20260701.md` to decide whether the current venue path needs more experiments, more reviewer examples, or only template production.
6. Decide whether the manual audit needs a second annotator before submission or can remain a transparent sanity check.
7. Decide after advisor review whether the issue-bundle case study should remain appendix material or become a main-paper table/figure.
8. Keep the offline-full20/partial16 empirical framing unless MiMo balance is restored and a fresh full20 rerun passes the same checks.
9. Fold the reproducibility appendix into the target paper format after figures and bibliography are finalized.
10. Re-audit all result claims after any fresh run changes the dashboard or case tables.

## Submission-Readiness Blockers

- No fresh full20 live rerun is available while MiMo returns `402 Insufficient account balance`; this blocks broad benchmark-style claims, not the conservative framework draft.
- Figure SVG/PDF drafts exist, but final venue-template placement is not checked.
- Bibliography keys are internally consistent and cleaned, but final target-venue records are not verified.
- The empirical result is diagnostic and small; the paper must not claim broad review-quality improvement.
