# Abstract Revision Audit

Date: 2026-07-01

Status: paper-writing audit for the abstract in `PAPER_CLEAN_BODY_DRAFT_20260701.md` and `PAPER_CONTINUOUS_DRAFT_20260701.md`.

## Reason For Revision

The previous abstract was accurate but too dense. It included:

- 13 raw issue rows;
- 9 clusters;
- 8/9 manual audit;
- direct quote-grounded negative count of 0;
- multiple final-view hygiene zero counts;
- conservative framework positioning.

This made the abstract read like a compact dashboard rather than a paper argument.

## Revised Abstract Strategy

The revised abstract follows this order:

1. Problem: fluent LLM review text can collapse support, contestation, and speculation.
2. Method: DrMAS maintains ReviewState objects and separates direct negatives from obligation-grounded issues.
3. Main diagnostic result: 9 obligation-grounded issue clusters, 8 manually judged valid or defensible.
4. Safety signal: zero active negative-grounding conflicts and zero unlinked negative evidence.
5. Mandatory caveat: direct quote-grounded negative lane yields no verified direct negatives.
6. Positioning: conservative state maintenance and repair, not autonomous review generation.

## What Changed

| Prior abstract element | Revised handling |
| --- | --- |
| 13 raw issue rows | Removed from abstract; retained in experiment table. |
| 9 issue clusters | Kept as the headline empirical count. |
| 8/9 manual audit | Kept, phrased as manually judged valid or defensible. |
| Four hygiene zero metrics | Reduced to two representative final-view validation checks: active negative-grounding conflicts and unlinked negative evidence. Full list remains in experiments. |
| "hygiene diagnostics" | Rephrased once as "final-view validation" for paper-facing clarity. |
| Direct-negative count 0 | Kept explicitly as a limitation and motivation. |
| "unconstrained review generation" | Tightened to "autonomous review generation." |

## Second Pass Compression

After the method-lifecycle and compact issue-bundle table edits, the abstract was compressed again to read less like a metric ledger. The current version keeps the same evidence but uses five sentence roles:

1. fluency can collapse support, contestation, and speculation;
2. DrMAS treats reviewing as typed ReviewState maintenance;
3. the paper's central distinction is direct quote negatives versus obligation-grounded issues;
4. the diagnostic result is 9 clusters, 8 manually judged valid or defensible, with two final-view validation protections clean;
5. the strict direct-quote negative lane remains at 0, so the claim is conservative state maintenance rather than autonomous review generation.

No result claim changed in this compression pass.

## Guardrails Preserved

The revised abstract still avoids all unsafe claims:

- it does not claim broad review-quality improvement;
- it does not claim autonomous defect discovery;
- it does not hide direct quote-grounded negative count 0;
- it does not present 13 rows as independent defects;
- it does not present 8/9 as population precision;
- it keeps the result diagnostic.

## Current Abstract Result Sentence

> On a 20-paper hard-negative diagnostic set, DrMAS verifies 9 obligation-grounded review issue clusters, 8 of which are manually judged valid or defensible, while maintaining zero active negative-grounding conflicts and zero unlinked negative evidence in the reported artifacts.

## Remaining Abstract Question

Advisor/internal review should decide whether the direct-negative zero sentence belongs in the abstract for the target venue. Current default: keep it in the abstract because hiding it creates a worse reviewer trust problem.
