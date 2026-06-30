# Advisor Review Packet

Date: 2026-07-01

Status: internal review index for the current DrMAS paper package. This is not paper body text.

## What To Read First

1. `PAPER_CLEAN_BODY_DRAFT_20260701.md`
   - Best current manuscript body.
   - Uses paper-facing language, rendered SVG figure references, and conservative empirical framing.
   - Engineering run identifiers are now moved out of the main narrative and into supporting documents.
   - Abstract now uses 9 clusters as the headline result and leaves raw row count to the experiment table.

2. `PAPER_READINESS_AUDIT_20260701.md`
   - Skeptical audit of what the paper can and cannot claim.
   - Best file for checking whether the story is overclaiming.

3. `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md`
   - Maps each paper-level claim to current evidence, allowed wording, and forbidden overclaims.

4. `PAPER_REVIEWER_PREMORTEM_20260701.md`
   - Reviewer-risk audit: likely objections, honest responses, forbidden responses, and concrete manuscript actions.
   - Best file for deciding whether the current story is being positioned for the right kind of venue.

5. `PAPER_VENUE_FIT_DECISION_20260701.md`
   - Recommends a systems/method or human-AI review-support framing and explains why benchmark-heavy venues need more evidence.
   - Best file for deciding whether to proceed to template conversion or strengthen experiments first.

6. `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md`
   - Maps paper concepts to code anchors, scripts, run artifacts, and metric checks.
   - Use this for traceability, not as main-text narrative.

7. `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md`
   - Explains one verified obligation-grounded issue bundle step by step.
   - Best file for checking whether the claim-anchor, inventory-anchor, missing-entity, and recovery story is understandable.

8. `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md`
   - Defines the A/B/C/D cluster labels and reporting rules for the 8/9 manual quality statement.
   - Best file for checking whether the manual audit is being used conservatively.

9. `PAPER_ABSTRACT_REVISION_AUDIT_20260701.md`
   - Records why the abstract was simplified and which caveats remain visible.

10. `PAPER_TERMINOLOGY_GUIDE_20260701.md`
   - Defines paper-facing terms such as final-view validation, recovery action, diagnostic set, and verified issue cluster.
   - Best file for preventing the manuscript from drifting back into implementation-log wording.

11. `PAPER_REFERENCES_DRAFT_20260701.bib` and `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md`
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
2. Which venue family should this target first: systems/method, human-AI review support, peer-review automation workshop, or benchmark-heavy ML/NLP?
3. Should the paper foreground obligation-grounded issue bundles as the main conceptual contribution, or frame them as one mechanism inside a broader ReviewState lifecycle?
4. Is the conservative result sentence acceptable, or does the venue require a fresh full20 rerun before submission?
5. Should the direct quote-grounded negative lane with count 0 be in the abstract, or reserved for experiments/limitations?
6. Does the illustrative issue-bundle case study make the core mechanism clearer, or should it become a figure/table in the main paper?
7. Are the A/B/C manual-audit labels defined tightly enough for advisor review, or does this need a second annotator before submission?
8. Is the final-view validation terminology clearer than the earlier hygiene wording for the intended venue?
9. Which pre-mortem risk is most likely for the target venue: empirical scale, direct-negative zero, deterministic seeds, missing-ablation skew, or engineering-artifact framing?
10. Does the related-work framing need more peer-review-specific references before submission?

## Known Non-Negotiables

- Do not claim DrMAS discovers many true flaws.
- Do not claim direct negative evidence discovery is solved.
- Do not headline raw row count as independent defects.
- Do not describe the partial16 run as a fresh full20 result.
- Do not hide the 0 direct quote-grounded negative count.
- Do not present recovery as accept/reject correction.

## Next Production Step

After advisor feedback, choose the venue family before target-template integration:

- decide whether to target systems/method, human-AI review support, peer-review automation workshop, or benchmark-heavy ML/NLP;
- convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the venue template;
- place SVG/PDF figures and check scaling/cropping;
- export final venue-style BibTeX;
- fold the reproducibility appendix into the target format;
- re-audit all claims after any fresh run or template conversion.
