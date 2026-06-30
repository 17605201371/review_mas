# Advisor Review Packet

Date: 2026-07-01

Status: internal review index for the current DrMAS paper package. This is not paper body text.

## What To Read First

1. `PAPER_CLEAN_BODY_DRAFT_20260701.md`
   - Best current manuscript body.
   - Uses paper-facing language, rendered SVG figure references, and conservative empirical framing.
   - Engineering run identifiers are now moved out of the main narrative and into supporting documents.

2. `PAPER_READINESS_AUDIT_20260701.md`
   - Skeptical audit of what the paper can and cannot claim.
   - Best file for checking whether the story is overclaiming.

3. `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md`
   - Maps each paper-level claim to current evidence, allowed wording, and forbidden overclaims.

4. `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md`
   - Maps paper concepts to code anchors, scripts, run artifacts, and metric checks.
   - Use this for traceability, not as main-text narrative.

5. `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md`
   - Explains one verified obligation-grounded issue bundle step by step.
   - Best file for checking whether the claim-anchor, inventory-anchor, missing-entity, and recovery story is understandable.

6. `PAPER_REFERENCES_DRAFT_20260701.bib` and `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md`
   - Draft bibliography and remaining metadata risks.

## Current Thesis

The paper should be reviewed as a conservative ReviewState framework paper:

> Reliable LLM-assisted peer review requires auditable ReviewState maintenance, because many reviewer issues are not direct negative quotes but claim-inventory-obligation mismatches that must be verified and rendered separately from speculative concerns.

The paper should not be reviewed as a broad benchmark paper, autonomous reviewer, or accept/reject classifier.

## Current Empirical Claim

The defensible main result is:

> On a 20-paper hard-negative diagnostic set, DrMAS verifies 9 obligation-grounded review issue clusters, 8 of which are manually judged valid or defensible, while maintaining zero active negative-grounding conflicts and zero unlinked negative evidence in the reported artifacts.

Mandatory caveats:

- direct quote-grounded reviewer negatives remain 0;
- the main full20 result is an offline recomputation over a completed run;
- the freshest live sanity rerun is partial16, not full20;
- issue diversity is narrow and missing-ablation heavy;
- most verified issue rows come from deterministic reviewer seeds, not mature autonomous Critique discovery.

## Figures In The Draft

Figure assets are in `paper_figures/`:

- `figure1_reviewstate_lifecycle.svg`
- `figure2_critical_content_lanes.svg`
- `figure3_verification_funnel.svg`
- `figure4_non_destructive_recovery.svg`

They parse and render, but still need target-template placement and visual QA.

## Questions For Advisor Review

1. Is the ReviewState-maintenance framing strong enough for the intended venue, given that the empirical result is diagnostic rather than broad?
2. Should the paper foreground obligation-grounded issue bundles as the main conceptual contribution, or frame them as one mechanism inside a broader ReviewState lifecycle?
3. Is the conservative result sentence acceptable, or does the venue require a fresh full20 rerun before submission?
4. Should the direct quote-grounded negative lane with count 0 be in the abstract, or reserved for experiments/limitations?
5. Does the illustrative issue-bundle case study make the core mechanism clearer, or should it become a figure/table in the main paper?
6. Does the related-work framing need more peer-review-specific references before submission?

## Known Non-Negotiables

- Do not claim DrMAS discovers many true flaws.
- Do not claim direct negative evidence discovery is solved.
- Do not headline raw row count as independent defects.
- Do not describe the partial16 run as a fresh full20 result.
- Do not hide the 0 direct quote-grounded negative count.
- Do not present recovery as accept/reject correction.

## Next Production Step

After advisor feedback, the next mechanical step is target-template integration:

- convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the venue template;
- place SVG/PDF figures and check scaling/cropping;
- export final venue-style BibTeX;
- fold the reproducibility appendix into the target format;
- re-audit all claims after any fresh run or template conversion.
