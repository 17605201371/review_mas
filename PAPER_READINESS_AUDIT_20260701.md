# Paper Readiness Audit

Date: 2026-07-01

Status: narrative/readiness audit, not a result artifact. This document checks whether the current DrMAS paper story can survive review as a conservative ReviewState paper. It is deliberately skeptical: the goal is to identify what is already defensible, what is fragile, and what should not be claimed.

## Executive Judgment

The paper is now narratively coherent but not yet submission-ready.

The strongest current version is a conservative systems/method paper:

> DrMAS reframes LLM-assisted reviewing as ReviewState maintenance. It separates direct quote-grounded negative evidence from obligation-grounded reviewer issues, verifies the latter through claim-inventory-obligation bundles, audits the final view for false-negative artifacts, and supports non-destructive contested recovery.

This story is defensible because it matches the current artifacts:

- continuous manuscript draft exists;
- figures exist as Mermaid sources plus manually redrawn SVG/PDF drafts;
- draft citation keys and candidate bibliography exist;
- P28.6 metrics support the central ReviewState/hygiene claim;
- the paper explicitly admits direct quote-grounded negative discovery remains unsolved.

The paper is not ready for a strong benchmark-performance claim. The current result is diagnostic and conservative, not broad:

- hardneg20 is small;
- fresh live rerun is partial16 only;
- verified issue diversity is narrow;
- most verified issue rows come from deterministic seeds;
- direct quote-grounded negative count is 0.

## Current Asset Inventory

| Asset | File | Status |
| --- | --- | --- |
| Narrative blueprint | `PAPER_NARRATIVE_BLUEPRINT_20260701.md` | Current guardrail |
| Claims/evidence matrix | `PAPER_CLAIMS_EVIDENCE_MATRIX_20260701.md` | Current claim audit |
| Continuous manuscript | `PAPER_CONTINUOUS_DRAFT_20260701.md` | Paper-facing draft; still not camera-ready |
| Clean body draft | `PAPER_CLEAN_BODY_DRAFT_20260701.md` | Best current advisor/internal-review manuscript body; main experiment narrative no longer exposes engineering run IDs |
| Abstract revision audit | `PAPER_ABSTRACT_REVISION_AUDIT_20260701.md` | Records why the abstract now headlines clusters rather than raw rows |
| Advisor review packet | `PAPER_ADVISOR_REVIEW_PACKET_20260701.md` | File index, thesis, caveats, and review questions for advisor/internal review |
| Reviewer pre-mortem | `PAPER_REVIEWER_PREMORTEM_20260701.md` | Operational risk audit with likely objections, honest responses, and concrete manuscript actions |
| Issue-bundle case study | `PAPER_REVIEW_ISSUE_CASE_STUDY_20260701.md` | Concrete SpecDec++ example showing claim anchor, inventory anchor, missing ablation, and non-destructive recovery |
| Manual audit protocol | `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md` | Defines A/B/C/D cluster labels and conservative reporting rules for manual audit |
| Manuscript skeleton | `PAPER_MANUSCRIPT_SKELETON_20260701.md` | Structural backup |
| Production checklist | `PAPER_MANUSCRIPT_PRODUCTION_CHECKLIST_20260701.md` | Tracks remaining non-body work |
| Reproducibility appendix | `PAPER_REPRODUCIBILITY_APPENDIX_20260701.md` | Maps concepts to code anchors and artifacts |
| Empirical framing decision | `PAPER_EMPIRICAL_FRAMING_DECISION_20260701.md` | Defines offline-full20/partial16 conservative framing |
| Introduction | `PAPER_INTRODUCTION_DRAFT_20260701.md` | Folded into continuous draft |
| Method | `PAPER_METHOD_SECTION_DRAFT_20260701.md` | Folded into continuous draft |
| Experiments | `PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md` | Folded into continuous draft |
| Related work | `PAPER_RELATED_WORK_DRAFT_20260701.md` | Superseded by continuous draft plus BibTeX keys |
| Bibliography candidates | `PAPER_BIBLIOGRAPHY_CANDIDATES_20260701.md` | API-verified candidates and provenance notes |
| Draft BibTeX | `PAPER_REFERENCES_DRAFT_20260701.bib` | Cleaned drafting records, not final venue export |
| Bibliography audit | `PAPER_BIBLIOGRAPHY_AUDIT_20260701.md` | Record-level metadata risks and sources |
| Figure specs | `PAPER_FIGURE_SPECS_20260701.md` | Conceptual figure guardrails |
| Renderable figure draft | `PAPER_FIGURES_DRAFT_20260701.md` and `paper_figures/*.{mmd,svg,pdf}` | SVG/PDF drafts rendered; template placement pending |
| Main metrics | `P28_6_CONFLICTFIX_TARGETREFINE2_194911_*` | Main offline full20 recompute |
| Fresh sanity run | `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*` | Partial16 only; stopped by MiMo 402 |

## Evidence Ledger

### Main Offline Full20 Result

Source: `P28_6_CONFLICTFIX_TARGETREFINE2_194911_HARDNEG20_DASHBOARD.md/json`.

Supported paper-facing facts:

| Metric | Value | Paper use |
| --- | ---: | --- |
| papers | 20 | hardneg20 diagnostic setting |
| review_negative_verified_count | 0 | direct quote-negative lane remains unsolved |
| verified_review_issue_count | 13 | row count only, not headline |
| verified_review_issue_cluster_count | 9 | main system output count |
| duplicate_review_issue_row_count | 4 | reason to prefer clusters over rows |
| manual A/B clusters | 8/9 | conservative quality statement |
| reviewer_candidate_review_issue_critique_payload_count | 2 | shows Critique-driven recall is weak |
| reviewer_candidate_review_issue_deterministic_seed_count | 11 | deterministic seeds dominate |
| verified_missing_ablation_cluster_count | 6 | issue distribution is missing-ablation heavy |
| mark_contested_commit_count | 14 | non-destructive recovery signal |
| recovery_case_verified_review_issue_repair | 6 | conservative recovery count |
| negative_grounding_conflict_count | 0 | hygiene success |
| negative_semantic_anchor_conflict_count | 0 | hygiene success |
| semantic_negative_without_review_relation_count | 0 | hygiene success |
| negative_evidence_unlinked_to_flaw | 0 | linkage protection |
| positive_or_neutral_negative_candidate_count | 0 | false-negative-evidence protection |

### Fresh Live Sanity Check

Source: `P28_6_CONFLICTFIX_MIMO_PARTIAL16_224133_*`.

Use only as consistency evidence:

- completed papers: 16/20;
- verified review issue clusters: 8;
- direct quote-grounded negatives: 0;
- mark-contested commits: 5;
- active conflict metrics: 0;
- stopped by `402 Insufficient account balance`.

Do not call this a fresh full20 rerun.

## Paper-Ready Claims

These claims are currently defensible if stated with caveats:

1. DrMAS treats LLM-assisted reviewing as ReviewState maintenance rather than direct review generation.
2. DrMAS separates direct quote-grounded negatives from obligation-grounded reviewer issues.
3. DrMAS verifies 9 obligation-grounded review issue clusters on hardneg20 offline recompute.
4. Manual audit judges 8 of 9 clusters valid or defensible.
5. Direct quote-grounded negative discovery remains weak, with count 0 in the current run.
6. Final-view hygiene removes measured false-negative-evidence artifacts in P28.6 artifacts.
7. Recovery is non-destructive: verified issues can mark supported claims as contested rather than downgrading them.

## Claims To Avoid

Do not write any of the following:

- DrMAS discovers many true flaws.
- DrMAS solves negative evidence discovery.
- DrMAS finds 13 defects.
- The model autonomously discovers review issues.
- The fresh full20 rerun confirms the result.
- Recovery fixes accept/reject decisions.
- DrMAS improves review quality broadly.
- The system handles diverse reviewer issue types.

## Likely Reviewer Attacks

### Attack 1: "This is only 20 papers."

Valid. The response is to frame hardneg20 as a diagnostic stress test for ReviewState hygiene, not a broad benchmark. The paper should avoid population-level performance claims.

Best response:

> We evaluate a diagnostic hard-negative set to stress the state lifecycle and false-negative-evidence failure modes. The contribution is the verified state-management mechanism, not a broad leaderboard result.

What would strengthen it for a broader empirical claim:

- fresh full20 rerun after MiMo is restored;
- repeated-seed stability;
- a second diagnostic set or oracle/reference-review upper-bound analysis.

### Attack 2: "The system does not find direct negative evidence."

Valid, but not fatal if the paper owns it. The direct lane has `review_negative_verified_count=0`.

Best response:

> Direct quote-grounded negative evidence is rare and remains unsolved. This motivates the second lane: obligation-grounded issue verification, which is distinct from copied negative quotes.

What would be unsafe:

- hiding `review_negative_verified_count=0`;
- calling obligation-grounded issues direct negative evidence.

### Attack 3: "The issues are mostly missing ablations."

Valid. Current cluster distribution is 6 missing-ablation clusters, 2 missing-baseline clusters, and 1 reproducibility cluster.

Best response:

> The current prototype primarily validates the issue-bundle mechanism on missing-ablation and missing-baseline style issues. Broader issue diversity is future work.

What would strengthen it:

- entity-level obligation extraction for protocol, efficiency, robustness, reproducibility;
- Critique-driven candidate recall beyond deterministic seeds.

### Attack 4: "The verified issues come from deterministic seeds, not autonomous critique."

Valid. Main offline recompute has 11 deterministic-seed rows and 2 critique-payload rows.

Best response:

> We do not claim autonomous broad issue discovery. Candidate generation and bundle verification are separated; this paper focuses on conservative verification and state hygiene.

What would strengthen it:

- improve Critique candidate recall;
- report seed/candidate source distribution transparently;
- use oracle/reference-review targets only for upper-bound evaluation, not as system input.

### Attack 5: "Manual audit is small and subjective."

Valid. Manual audit is 9 clusters.

Best response:

> Manual audit is used to sanity-check the conservative cluster-level result, not to establish broad statistical performance.

What would strengthen it:

- independent second annotator;
- adjudication criteria;
- case appendix with claim anchor, inventory anchor, missing entity, and counterevidence result.

Current mitigation: `PAPER_MANUAL_AUDIT_PROTOCOL_20260701.md` defines the A/B/C/D labels and explicitly forbids treating 8/9 as a population-level precision estimate.

### Attack 6: "The paper reads like engineering logs."

Partly valid. The continuous draft is readable, but some terms still expose implementation history.

Best response:

> Polish the paper around concepts: ReviewState, issue bundle, final-view hygiene, contested repair. Move implementation anchors and P28 history to appendix.

Concrete edit:

- keep P28.6 in experiments, not in title/abstract;
- reduce function names in main text;
- move code-anchor table to appendix.

## Narrative Decision

The paper should be submitted, if at all, as a conservative framework/mechanism paper, not as a benchmark paper.

Recommended one-sentence thesis:

> Reliable LLM-assisted peer review requires auditable ReviewState maintenance, because many reviewer issues are not direct negative quotes but claim-inventory-obligation mismatches that must be verified and rendered separately from speculative concerns.

Recommended result sentence:

> On hardneg20, DrMAS verifies 9 obligation-grounded issue clusters, 8 of which are judged valid or defensible by manual audit, while maintaining zero active negative-grounding conflicts and zero unlinked negative evidence.

Mandatory caveat sentence:

> The direct quote-grounded negative lane remains strict and produces no verified direct negatives in the current run.

## Readiness Scorecard

| Dimension | Score | Rationale |
| --- | ---: | --- |
| Thesis coherence | 8/10 | Strong and now consistent across docs |
| Method clarity | 7/10 | Clear lifecycle; still needs polish away from implementation history |
| Evidence honesty | 8/10 | Major limitations are visible |
| Empirical strength | 5/10 | Diagnostic hardneg20 only; framing decision is conservative |
| Figure readiness | 7/10 | SVG/PDF drafts exist and render; target-template placement still pending |
| Citation readiness | 7/10 | Cleaned BibTeX and audit exist; final venue export still pending |
| Submission readiness | 6.7/10 | Clean body draft and abstract polish exist; target template integration still pending |

## Next Work Priority

### Priority 1: Advisor/Internal Review

Goal: get feedback on the current conservative framework story before spending effort on target-template production.

Tasks:

- use `PAPER_ADVISOR_REVIEW_PACKET_20260701.md` as the entry point;
- use `PAPER_REVIEWER_PREMORTEM_20260701.md` to decide which risk matters most for the intended venue;
- ask whether the ReviewState-maintenance framing is venue-appropriate;
- ask whether the 0 direct-negative count should stay in the abstract or move to experiments/limitations;
- decide whether the concrete issue-bundle case study should remain text/appendix material or become a main-paper figure/table.

### Priority 2: Continue Manuscript Production Polish

Goal: move from the clean body draft to a submission-ready manuscript.

Tasks:

- convert `PAPER_CLEAN_BODY_DRAFT_20260701.md` into the target venue template;
- convert Markdown table captions into proper paper captions;
- make limitations concise but visible;
- fold the reproducibility appendix into the target paper format after deciding venue/template constraints.

### Priority 3: Render Or Redraw Figures

Goal: place the rendered figure assets into the target paper template and perform visual QA.

Tasks:

- verify line wrapping and labels after template placement;
- check scaling, cropping, and grayscale readability;
- keep direct negative count 0 and row-to-cluster funnel visible.

### Priority 4: Finalize Bibliography

Goal: replace the cleaned draft records in `PAPER_REFERENCES_DRAFT_20260701.bib` with final target-venue exports.

Tasks:

- export entries from DBLP/ACL Anthology/arXiv/Crossref;
- verify author lists and venues;
- decide whether to add more LLM peer-review references.

### Priority 5: Decide Empirical Path

Current framing:

- keep offline full20 as the main diagnostic result for the conservative framework paper;
- keep partial16 as the freshest live sanity check;
- do not claim a fresh full20 rerun.

If MiMo balance returns:

- rerun fresh full20 P28.6;
- regenerate dashboard/case/recovery tables;
- re-audit all result claims.

If MiMo remains blocked:

- keep offline full20 as main result;
- keep partial16 as live sanity check;
- explicitly say hardneg20 is diagnostic.

## Bottom Line

The current package is good enough for an internal full-paper draft and for advisor-level review. It is not yet ready for submission. The decisive remaining work is not more narrative invention; it is final template polish, final venue-style bibliography export, and either a fresh full20 rerun for stronger empirical claims or disciplined maintenance of the conservative offline-full20/partial16 framing.
