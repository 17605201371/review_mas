# Paper Terminology Guide

Date: 2026-07-01

Status: paper-facing terminology guardrail. This is not paper body text.

## Purpose

The current narrative is strongest when it reads as a ReviewState framework paper rather than a development log. This guide records the preferred main-text terms and the implementation terms that should stay in appendices or artifact tables.

## Preferred Main-Text Terms

| Prefer | Avoid in main text | Notes |
| --- | --- | --- |
| final-view validation | hygiene | "Hygiene" can remain in metric names, code anchors, and historical audit docs. |
| recovery action | patch | "Patch" is implementation language; use only in appendix/code mapping. |
| audited view | dashboard | Use dashboard only when naming generated artifacts. |
| diagnostic set | benchmark | Current evidence is diagnostic, not broad benchmark performance. |
| obligation-grounded review issue | negative evidence | Keep this distinct from direct quote-grounded negatives. |
| direct quote-grounded negative | reviewer-inferred issue | Do not collapse these lanes. |
| verified issue cluster | defect | Clusters are review-worthy concerns, not independent defects. |
| live sanity check | fresh full20 rerun | The current live rerun is partial16 only. |

## Required Distinctions

- `review_negative_verified_count` is the direct quote-grounded negative lane and remains 0.
- `verified_review_issue_cluster_count` is the obligation-grounded issue lane and is the paper headline.
- Raw issue rows are not independent defects.
- Manual A/B labels are a small sanity-check audit, not population precision.
- Recovery marks supported claims as contested; it does not fix accept/reject decisions.

## Where Implementation Terms Are Allowed

Implementation terms are allowed in:

- `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md`;
- generated artifact names;
- code-anchor tables;
- commands and regeneration instructions;
- historical audit documents.

Implementation terms should be minimized in:

- abstract;
- introduction;
- method overview;
- discussion;
- conclusion.

## Current Text Status

`PAPER_CLEAN_BODY_DRAFT_20260701.md` and `PAPER_CONTINUOUS_DRAFT_20260701.md` now use "final-view validation" in the main paper prose. Some metric names and supporting audit files still use "hygiene" because those are artifact-compatible labels rather than paper-facing claims.
