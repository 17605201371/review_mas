# Reviewer Pre-Mortem

Date: 2026-07-01

Status: pre-submission risk audit for the current DrMAS paper narrative. This is not paper body text and not a new experiment.

## Current Submission Bet

The paper is currently viable only as a conservative framework/mechanism paper:

> DrMAS treats LLM-assisted peer review as auditable ReviewState maintenance. It verifies obligation-grounded review issue bundles, keeps direct quote-grounded negatives separate, performs final-view validation, and supports non-destructive contested recovery.

The paper is not currently viable as:

- a broad autonomous review-generation benchmark;
- a system that discovers many direct negative quotes;
- an accept/reject decision system;
- a statistically strong empirical performance paper.

The clean body draft already makes this framing clear. The remaining risk is whether reviewers accept a diagnostic, mechanism-first paper with a small empirical setting.

## Highest-Risk Reviews

### Review A: "This is not enough empirical evidence."

Likely rating impact: high.

Why the criticism is fair:

- main setting is a 20-paper diagnostic set;
- fresh live rerun is partial16, not full20;
- manual audit covers 9 clusters;
- there is no repeated-seed stability study yet.

What the paper can honestly say:

> We evaluate a diagnostic hard-negative setting designed to stress ReviewState validation and reviewer-issue verification. The result is evidence for a conservative state-maintenance mechanism, not a broad benchmark claim.

What the paper must not say:

- "DrMAS broadly improves review quality."
- "The result is statistically representative."
- "The fresh full20 rerun confirms the result."

Concrete manuscript action:

- Keep "diagnostic" in the abstract, experiment setup, and conclusion.
- Keep the main result as 9 clusters and 8/9 manual A/B clusters.
- Keep partial16 framed as live sanity evidence only.
- Add repeated-seed or second-dataset claims only after new experiments exist.

### Review B: "The direct negative evidence result is zero."

Likely rating impact: medium to high.

Why the criticism is fair:

- `review_negative_verified_count=0` in the authoritative result;
- direct quote-grounded negative discovery remains weak.

Why it is not fatal:

- the paper's central point is that many review issues are not copied negative quotes;
- the strict direct lane prevents author limitations, neutral inventory, and quote-bank artifacts from being mislabeled as reviewer negatives;
- obligation-grounded issue bundles are reported separately.

What the paper can honestly say:

> The zero direct-negative count is a limitation and a design motivation. It shows why direct quote-grounded negatives and reviewer-inferred issue bundles must be separated.

Concrete manuscript action:

- Keep one explicit sentence about zero direct negatives in the abstract or early experiments.
- Do not let readers discover the zero only in a table.
- Use the SpecDec++ case study to explain why the inventory quote is not a negative quote.

### Review C: "The system is not autonomous; deterministic seeds dominate."

Likely rating impact: medium.

Why the criticism is fair:

- verified issue rows are mostly deterministic reviewer seeds;
- Critique-payload candidate rows are only 2 in the main result.

What the paper can honestly say:

> Candidate generation and issue verification are separated. This paper evaluates conservative bundle verification and final-view validation, not mature autonomous issue discovery.

What the paper must not say:

- "The model autonomously discovers reviewer issues."
- "Critique-driven discovery is solved."

Concrete manuscript action:

- Keep source distribution in Table 1.
- In limitations, say Critique-driven recall is future work.
- Keep the deterministic-seed explanation explicit: seeds are auditable stress targets for verifier behavior, not autonomous discovery evidence.

### Review D: "The issues are mostly missing ablations."

Likely rating impact: medium.

Why the criticism is fair:

- current clusters are missing-ablation heavy;
- issue-bundle diversity is narrow.

What the paper can honestly say:

> The current prototype primarily validates missing-ablation and missing-baseline issue-bundle verification. Broader protocol, robustness, efficiency, and reproducibility coverage is future work.

Concrete manuscript action:

- Keep the issue-type distribution visible.
- Avoid saying "diverse reviewer issues."
- Use "issue-bundle mechanism" rather than "general flaw finder."

### Review E: "Manual audit is subjective and too small."

Likely rating impact: medium.

Why the criticism is fair:

- manual audit is 9 clusters;
- no second annotator or adjudication protocol is currently documented.

What the paper can honestly say:

> Manual audit is used as a sanity check on the conservative cluster-level result, not as a broad statistical evaluation.

Concrete manuscript action:

- Keep A/B/C cluster labels transparent.
- Include the SpecDec++ case study as a concrete audit trail.
- If time permits, define A/B/C criteria in the appendix.
- Do not turn 8/9 into a precision estimate over a population.

### Review F: "This is an engineering artifact rather than a research contribution."

Likely rating impact: high if the narrative is sloppy.

Why the criticism could happen:

- implementation history is long;
- artifact names and run IDs can make the paper feel like a log;
- many contributions are validation and state-management mechanisms.

What the paper can honestly say:

> The contribution is not a collection of implementation fixes. It is a review-specific state lifecycle: typed claims, evidence lanes, issue bundles, final-view validation, and non-destructive recovery.

Concrete manuscript action:

- Keep P28/run identifiers out of the clean body.
- Put code anchors and regeneration commands in the reproducibility appendix.
- Lead with ReviewState semantics, not implementation chronology.
- Keep "final-view validation" in the final venue version; avoid reverting to informal implementation-log wording.

### Review G: "Why should we trust the case study?"

Likely rating impact: low to medium.

Why the criticism is fair:

- one case study can be cherry-picked;
- the selected case is still a missing-ablation example.

What the paper can honestly say:

> The case study is explanatory, not statistical. It shows how a verified issue bundle is represented and why neutral inventory should not be counted as direct negative evidence.

Concrete manuscript action:

- Keep case study language explanatory.
- Do not use it as the main quantitative result.
- Keep the compact main-text table focused on claim anchor, inventory anchor, missing relation, verification status, and recovery action.

## Abstract-Level Risk

Current abstract is honest but dense. The biggest abstract risk is that it tries to carry too many caveats at once: 13 rows, 9 clusters, 8/9 manual audit, direct negatives zero, final-view validation zeros, and framework framing.

Safer abstract structure:

1. Problem: fluent reviews collapse support, contestation, and speculation.
2. Method: ReviewState with two critical-content lanes and non-destructive recovery.
3. Result: 9 issue clusters, 8/9 valid or defensible, final-view validation protections clean.
4. Caveat: direct quote-grounded negative lane remains strict and yields zero verified direct negatives.
5. Claim: conservative state maintenance, not autonomous review generation.

Potential edit:

> On a 20-paper diagnostic set, DrMAS verifies 9 obligation-grounded review issue clusters, 8 of which are manually judged valid or defensible, while maintaining zero active negative-grounding conflicts and zero unlinked negative evidence. The direct quote-grounded negative lane remains strict and yields no verified direct negatives, underscoring the need to separate copied negative quotes from reviewer-inferred issue bundles.

## Venue-Fit Decision

If targeting a systems, NLP infrastructure, or human-AI review-support venue:

- current framing is plausible;
- emphasize state semantics, verifiability, and lifecycle repair;
- keep empirical claims diagnostic.

If targeting a benchmark-heavy ML venue:

- current evidence is probably too small;
- require fresh full20, repeated seeds, and ideally a second diagnostic set;
- consider moving this work into a methods/positioning paper first.

If targeting a peer-review automation venue:

- add more related work on LLM reviewing and peer-review assistance;
- foreground why state maintenance is safer than free-form review generation;
- include more reviewer-facing examples.

## Exact Edits To Consider Next

1. Shorten the abstract by reducing metric density, while keeping the zero direct-negative caveat visible.
2. Add a compact A/B/C manual-audit criteria box or appendix subsection.
3. After venue selection, decide whether the compact SpecDec++ table stays in the main text or moves to the appendix for space.
4. Keep final-view validation terminology consistent during venue-template conversion.
5. Add one sentence in related work contrasting DrMAS with free-form LLM review generation and citation-only grounding systems if the target venue needs stronger positioning.

## Things Not To Do Next

- Do not chase a larger `review_negative_verified_count` by relaxing quote-grounded negative validation.
- Do not hide the 0 direct-negative result.
- Do not report raw issue rows as independent defects.
- Do not rerun MiMo full20 until account access is fixed and the run can complete.
- Do not add a benchmark-performance conclusion unless new experiments support it.
- Do not let the paper drift back into P28 development chronology.

## Bottom Line

The paper's most likely failure mode is not that the current story is incoherent. It is that reviewers may evaluate it as the wrong kind of paper. The narrative should make the intended category unmistakable: DrMAS is a conservative ReviewState verification and repair framework, with diagnostic evidence that the lifecycle can separate support, direct negatives, obligation-grounded issues, stale artifacts, and contested recovery.
