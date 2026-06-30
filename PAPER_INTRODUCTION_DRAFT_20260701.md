# Introduction Section Draft

Date: 2026-07-01

This draft is written to match the current P28.6 evidence. It intentionally avoids presenting DrMAS as a broad autonomous flaw finder or an accept/reject classifier. The central claim is that LLM-assisted reviewing needs explicit ReviewState maintenance: claims, evidence, review issues, conflicts, hygiene checks, and recovery actions must be represented and audited before they are rendered as a final review.

## 1. Introduction

Large language models can generate plausible peer-review text, but plausibility is not the same as review reliability. A useful review needs to preserve several distinctions at once: what the paper actually claims, what evidence supports each claim, which concerns are grounded in the paper, which concerns are reviewer-inferred, which supported claims are still contested, and which weak signals should remain speculative rather than become asserted defects. In a single-pass review-generation pipeline, these distinctions are easy to collapse into fluent prose. The result can look coherent while losing track of the underlying review state.

This problem is especially visible for negative or critical review content. Some criticisms can be grounded in a direct paper quote: a result may underperform a baseline, a table may contradict a claimed improvement, or an evaluation protocol may explicitly invalidate a claim. Many useful reviewer concerns, however, are not written as negative sentences in the paper. A paper usually does not say that it lacks a decisive ablation, omits a relevant baseline family, or leaves a method insufficiently specified for reproduction. These concerns are reviewer-inferred: they arise from a mismatch between a claim, the evidence obligations implied by that claim, and the inventory of experiments or method details that the paper actually provides.

Treating all critical content as "negative evidence" is therefore too narrow. It encourages systems either to overfit to copied negative-looking text or to fabricate defects when no such text exists. A safer review assistant should instead maintain a structured state that separates direct quote-grounded negatives from obligation-grounded reviewer issues. Direct negatives require a copied quote that itself supports the reviewer-negative relation. Obligation-grounded issues require a different evidence package: a real claim anchor, an observed inventory anchor, a concrete missing or mismatched entity, and a counterevidence check showing that the paper does not already satisfy the obligation.

We introduce DrMAS, a ReviewState-driven framework for LLM-assisted reviewing. DrMAS does not ask an LLM to directly emit the final review. It incrementally builds a structured ReviewState containing claims, evidence records, flaw or concern candidates, verified review issue bundles, conflict relations, recovery patches, and final-view hygiene diagnostics. The final review is rendered from this audited state rather than from raw model prose.

The core design is a two-lane treatment of critical review content. The first lane is direct quote-grounded negative evidence. It is deliberately strict: a record counts only when a paper-grounded quote, semantic negative relation, reviewer-negative relation, real claim binding, and flaw or issue linkage all succeed. The second lane is obligation-grounded review issue verification. A reviewer issue can be verified without a copied negative quote when it is supported by a claim-inventory-obligation mismatch. This lets DrMAS represent concerns such as missing ablations, missing baseline families, and reproducibility gaps without pretending that the paper itself contains a negative sentence.

DrMAS also treats recovery as state repair, not as decision correction. When a claim has real positive support but is contested by a verified issue, the preferred repair is to mark the claim as supported-but-contested. The system does not need to destructively downgrade the claim status to expose the concern. This is important for paper review: a strong contribution can be genuinely supported while still being limited by missing ablations, incomplete comparisons, or insufficient reproducibility details.

We evaluate DrMAS on the hardneg20 diagnostic set, which stresses negative-evidence and reviewer-issue handling. The current P28.6 result should be read conservatively. The direct quote-grounded negative lane remains strict and produces no verified direct negatives. The main result is instead obligation-grounded issue verification: on a hardneg20 offline recompute, DrMAS verifies 13 review issue rows that deduplicate to 9 issue clusters, with manual audit judging 8 of the 9 clusters valid or defensible. The final-view hygiene checks remain clean: active negative-grounding conflicts, semantic anchor conflicts, semantic negatives without verified review relation, unlinked negative evidence, and positive/neutral negative candidates are all zero in the authoritative P28.6 artifacts.

These results support a narrower but stronger claim than broad autonomous review generation. DrMAS shows that review-critical information can be represented as auditable state objects, verified through explicit lifecycle checks, and surfaced through non-destructive recovery. The system does not yet solve direct quote-grounded negative discovery, broad issue diversity, or autonomous Critique-driven candidate recall. Most current verified issues are missing-ablation heavy and many come from deterministic reviewer seeds. We treat these as limitations rather than hiding them behind aggregate counts.

This paper makes the following contributions:

1. We formulate LLM-assisted reviewing as ReviewState maintenance rather than direct review generation, representing claims, evidence, reviewer issues, conflicts, hygiene diagnostics, and recovery actions as structured state.
2. We distinguish direct quote-grounded negative evidence from obligation-grounded review issues, preventing reviewer-inferred absence concerns from being falsely counted as copied paper-negative quotes.
3. We introduce a conservative review issue bundle verifier that checks claim anchors, observed inventory anchors, concrete missing or mismatched entities, counterevidence, and review-worthiness before a concern enters the verified issue view.
4. We implement final-view hygiene checks that suppress common false-negative artifacts, including positive or neutral text misused as negative evidence, stale absence records, quote-bank artifacts, retrieval gaps, and unlinked negative evidence.
5. We show that verified issues can drive non-destructive recovery through contested relations, preserving supported claims while exposing unresolved review concerns.

The broader lesson is that reliable LLM-assisted reviewing is not only a prompting problem. It is a state-management problem. A review assistant needs to know not just what it wants to say, but why each statement is allowed to appear in the final review and what status it has in the review lifecycle.

## Drop-In Short Introduction

LLM-generated peer reviews can be fluent while losing track of what is supported, contested, or merely speculative. This is particularly problematic for critical review content. Some criticisms are directly quote-grounded, but many useful reviewer issues are not written as negative sentences in the paper; they arise from mismatches between a paper claim, the evidence obligations implied by that claim, and the experiments or method details the paper actually provides. We introduce DrMAS, a ReviewState-driven review assistant that maintains claims, evidence, reviewer issues, conflicts, hygiene diagnostics, and recovery actions as auditable state. DrMAS keeps direct quote-grounded negative evidence separate from obligation-grounded review issue bundles, allowing the system to verify concerns such as missing ablations, missing baselines, and reproducibility gaps without fabricating negative quotes. On hardneg20, the current P28.6 pipeline verifies 9 obligation-grounded issue clusters, 8/9 of which are manually judged valid or defensible, while maintaining zero active negative-grounding conflicts, zero unlinked negative evidence, and zero positive/neutral negative candidates. Direct quote-grounded negative discovery remains unsolved in the current run, so we present DrMAS as a conservative ReviewState verification and recovery framework rather than a broad autonomous flaw generator.

## Guardrails For Later Editing

Keep these statements in the intro:

- Direct quote-grounded negative discovery remains weak in P28.6.
- The headline result is 9 verified issue clusters and 8/9 manual A/B clusters, not 13 defects.
- The contribution is ReviewState maintenance, bundle verification, final-view hygiene, and non-destructive recovery.
- The fresh MiMo rerun is partial16 only; do not call it a full rerun unless a new full20 completes.

Avoid these statements:

- "DrMAS finds many true flaws."
- "DrMAS solves negative evidence discovery."
- "The model autonomously discovers reviewer issues."
- "Recovery fixes review decisions."
- "The system finds 13 defects."
