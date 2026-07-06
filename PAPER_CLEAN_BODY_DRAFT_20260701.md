# ReviewState Maintenance for Conservative LLM-Assisted Peer Review

## Abstract

Large language models can generate plausible peer-review text, but fluency can collapse what is supported, contested, or speculative. We present DrMAS, a ReviewState-driven framework that treats LLM-assisted reviewing as auditable state maintenance: claims, evidence, reviewer issues, conflicts, final-view validation, and recovery are represented as typed state objects. The key distinction is between direct quote-grounded negatives and obligation-grounded review issues, which are verified from a claim anchor, observed paper inventory, a concrete missing or mismatched entity, and counterevidence checks rather than from a copied negative sentence. On two accepted hardneg20 clean runs, DrMAS produces five recurring Critique-origin obligation-grounded review issue clusters, all manually judged valid or defensible, with manual-D total 0, harmful recovery total 0, and Critique-origin cluster Jaccard 1.000. These results support conservative ReviewState maintenance and repair, not autonomous review generation or accept/reject prediction.

## 1. Introduction

Large language models can generate plausible peer-review text, but plausibility is not the same as review reliability. A useful review needs to preserve several distinctions at once: what the paper actually claims, what evidence supports each claim, which concerns are grounded in the paper, which concerns are reviewer-inferred, which supported claims are still contested, and which weak signals should remain speculative rather than become asserted defects. In a single-pass review-generation pipeline, these distinctions are easy to collapse into fluent prose. The result can look coherent while losing track of the underlying review state.

This problem is especially visible for negative or critical review content. Some criticisms can be grounded in a direct paper quote: a result may underperform a baseline, a table may contradict a claimed improvement, or an evaluation protocol may explicitly invalidate a claim. Many useful reviewer concerns, however, are not written as negative sentences in the paper. A paper usually does not say that it lacks a decisive ablation, omits a relevant baseline family, or leaves a method insufficiently specified for reproduction. These concerns are reviewer-inferred: they arise from a mismatch between a claim, the evidence obligations implied by that claim, and the inventory of experiments or method details that the paper actually provides.

Treating all critical content as "negative evidence" is therefore too narrow. It encourages systems either to overfit to copied negative-looking text or to fabricate defects when no such text exists. A safer review assistant should instead maintain a structured state that separates direct quote-grounded negatives from obligation-grounded reviewer issues. Direct negatives require a copied quote that itself supports the reviewer-negative relation. Obligation-grounded issues require a different evidence package: a real claim anchor, an observed inventory anchor, a concrete missing or mismatched entity, and a counterevidence check showing that the paper does not already satisfy the obligation.

We introduce DrMAS, a ReviewState-driven framework for LLM-assisted reviewing. DrMAS does not ask an LLM to directly emit the final review. It incrementally builds a structured ReviewState containing claims, evidence records, flaw or concern candidates, verified review issue bundles, conflict relations, recovery actions, and final-view validation diagnostics. The final review is rendered from this audited state rather than from raw model prose.

The core design is a two-lane treatment of critical review content. The first lane is direct quote-grounded negative evidence. It is deliberately strict: a record counts only when a paper-grounded quote, semantic negative relation, reviewer-negative relation, real claim binding, and flaw or issue linkage all succeed. The second lane is obligation-grounded review issue verification. A reviewer issue can be verified without a copied negative quote when it is supported by a claim-inventory-obligation mismatch. This lets DrMAS represent concerns such as missing ablations, missing baseline families, and reproducibility gaps without pretending that the paper itself contains a negative sentence.

DrMAS also treats recovery as state repair, not as decision correction. When a claim has real positive support but is contested by a verified issue, the preferred repair is to mark the claim as supported-but-contested. The system does not need to destructively downgrade the claim status to expose the concern. This is important for paper review: a strong contribution can be genuinely supported while still being limited by missing ablations, incomplete comparisons, or insufficient reproducibility details.

We evaluate the current DrMAS pipeline on two accepted hardneg20 clean runs. Across these runs, five Critique-origin verified review issue clusters recur exactly. These clusters are obligation-grounded rather than direct quote-grounded negatives: each is verified through a claim anchor, observed paper inventory or quote evidence, a concrete missing or mismatched entity, and counterevidence checks. Manual audit labels the recurring clusters as A/B with zero D labels, while harmful recovery remains 0.

These results support a narrower but stronger claim than broad autonomous review generation. DrMAS shows that review-critical information can be represented as auditable state objects, verified through explicit lifecycle checks, and surfaced through non-destructive recovery. The system does not yet establish full39 generalization, accept/reject accuracy improvement, PPO or RL gains, or direct quote-grounded negative recall improvement. We treat these as limitations rather than hiding them behind aggregate counts.

This paper makes the following contributions:

1. We formulate LLM-assisted reviewing as ReviewState maintenance rather than direct review generation, representing claims, evidence, reviewer issues, conflicts, final-view validation diagnostics, and recovery actions as structured state.
2. We distinguish direct quote-grounded negative evidence from obligation-grounded review issues, preventing reviewer-inferred absence concerns from being falsely counted as copied paper-negative quotes.
3. We introduce a conservative review issue bundle verifier that checks claim anchors, observed inventory anchors, concrete missing or mismatched entities, counterevidence, and review-worthiness before a concern enters the verified issue view.
4. We implement final-view validation checks that suppress common false-negative artifacts, including positive or neutral text misused as negative evidence, stale absence records, quote-bank artifacts, retrieval gaps, and unlinked negative evidence.
5. We show that verified issues can drive non-destructive recovery through contested relations, preserving supported claims while exposing unresolved review concerns.

The broader lesson is that reliable LLM-assisted reviewing is not only a prompting problem. It is a state-management problem. A review assistant needs to know not just what it wants to say, but why each statement is allowed to appear in the final review and what status it has in the review lifecycle.

## 2. Related Work

### 2.1 LLM-Assisted Peer Review

Recent work studies whether large language models can provide useful feedback on research papers, summarize manuscripts, identify weaknesses, or assist reviewers during peer review \citep{liang2023llmfeedback,zhuang2025automatedreview,sun2025peerreview}. This literature highlights both the opportunity and the risk of automated scholarly review: generated feedback can appear useful, but review quality depends on whether claims, evidence, limitations, and criticisms are faithfully handled. Many systems evaluate generated review text directly: whether it is helpful, whether it overlaps with human reviews, or whether authors and reviewers perceive it as useful.

DrMAS addresses a complementary problem. Instead of treating review generation as the main object, it treats the intermediate review state as the object that must be maintained, audited, and repaired. This distinction matters because a fluent review can mix grounded strengths, unsupported criticisms, author-stated limitations, retrieval failures, and speculative concerns in the same prose. DrMAS therefore represents claims, evidence, reviewer issues, conflicts, and recovery actions as structured state before rendering the final review.

The current results should not be framed as showing that DrMAS is a better general review generator. The evidence supports a narrower claim: DrMAS can verify obligation-grounded review issue bundles and suppress measured false-negative-evidence artifacts on a diagnostic hard-negative set.

### 2.2 Retrieval-Augmented And Grounded Scientific Assistance

Retrieval-augmented generation and grounded scientific QA systems aim to reduce hallucination by conditioning generation on source documents and requiring evidence citations \citep{lewis2020rag,gao2023alce,wadden2020scifact}. In paper-review settings, this usually means retrieving relevant excerpts and asking the model to justify its comments with quotations or citations.

DrMAS uses grounding, but the central contribution is not retrieval alone. The system distinguishes paper quotes that directly support a claim from neutral inventory anchors that support an absence-style review issue. For example, an experiment table can be positive or neutral paper content while still serving as the observed inventory anchor for a missing-ablation concern. This lets DrMAS verify reviewer issues that are not directly expressed as negative paper sentences.

This is a key difference from a pure quote-grounding view. If a system requires every criticism to be backed by a copied negative quote, it will miss many real reviewer issues. If it relaxes quote requirements without state checks, it risks fabricating defects. DrMAS instead verifies a claim-inventory-obligation mismatch as a structured bundle.

### 2.3 Factuality, Attribution, And Evidence Verification

A large body of work studies factuality, attribution, and evidence verification for generated text \citep{rashkin2021attribution,thorne2018fever,wadden2020scifact}. These methods ask whether generated statements are supported by source material, whether citations are faithful, or whether an answer contradicts evidence.

DrMAS inherits the same concern but applies it to the lifecycle of a review. The unit of verification is not only a generated sentence. It can be a state object: a claim binding, an evidence record, a review issue bundle, a contested relation, or a recovery action. This state-level view makes it possible to ask more specific questions: whether evidence is grounded in the paper, whether it supports a real claim rather than a fallback artifact, whether a negative label is semantically appropriate, whether a reviewer issue is a direct negative or an obligation-grounded absence issue, and whether the final report is using stale or unlinked evidence.

The final-view validation metrics in our evaluation are examples of this state-level verification. Active negative-grounding conflicts, semantic anchor conflicts, semantic negatives without review relation, unlinked negative evidence, and positive/neutral negative candidates are tracked explicitly rather than hidden inside generated prose.

### 2.4 Multi-Agent Reviewing And Self-Correction

Agentic LLM systems often divide a task among roles, such as planner, retriever, verifier, critic, and editor \citep{wu2023autogen,li2023camel}. Self-correction systems ask models to critique and revise their own outputs, sometimes with tool use or external feedback \citep{madaan2023selfrefine,shinn2023reflexion}.

DrMAS uses multiple roles, but the paper should not frame the contribution as "more agents." The contribution is the persistent ReviewState that agents read and update. Without explicit state semantics, a critic can produce plausible objections that are not grounded, and a repair step can overwrite useful support while trying to fix a flaw. DrMAS constrains repair through typed operations such as contested relations, preserving supported claims while exposing verified issues.

This also explains why recovery is reported as state repair, not decision correction. The current system does not claim to fix accept/reject decisions. It exposes supported-but-contested claims, blocks unsafe downgrade behavior, and records repair attempts in the state.

### 2.5 Review-State And Argument-State Representations

Structured argumentation and evidence graphs represent claims, supports, attacks, and relations among evidence \citep{lawrence2020argumentmining,thorne2018fever,wadden2020scifact}. These lines of work are relevant because peer review is not just text generation; it is an argument about a paper's claims, evidence, limitations, and unresolved risks.

DrMAS can be positioned as a review-specific state representation. A ReviewState includes paper claims, evidence records, issue bundles, conflict relations, recovery logs, and final-view validation diagnostics. The review issue bundle is especially important: it represents a reviewer concern as a typed relation among a claim anchor, observed inventory, a missing or mismatched entity, and counterevidence checks.

This differs from ordinary argument mining because the state is operational. The system uses the state to decide whether evidence can count, whether a concern should be verified or remain diagnosis-pending, whether a claim should be marked contested, and whether the final report is allowed to render a flaw.

### 2.6 Positioning Summary

DrMAS sits at the intersection of LLM-assisted reviewing, grounded generation, factuality verification, and agentic self-correction. Its distinguishing claim is that reviewing should be treated as auditable state maintenance. The final review should not be trusted merely because it is fluent or quote-rich. It should be trusted only insofar as its claims, evidence, reviewer issues, conflicts, and repairs survive explicit state-level checks.

The current empirical evidence supports this positioning conservatively. DrMAS does not solve direct quote-grounded negative discovery and does not establish broad autonomous issue discovery. It does show that obligation-grounded review issues can be verified as state objects and that measured false-negative-evidence failure modes can be kept out of the final view.

## 3. Method

### 3.1 Overview

DrMAS treats LLM-assisted reviewing as a state maintenance problem. Instead of asking a model to directly produce a final review, the system incrementally builds a structured ReviewState, audits that state, and renders the final review from an audited view.

![Figure 1: ReviewState lifecycle](paper_figures/figure1_reviewstate_lifecycle.svg)

Figure 1. DrMAS treats LLM-assisted reviewing as ReviewState maintenance. The system extracts claims, grounds evidence, forms and verifies review issue bundles, audits the final view, and applies non-destructive recovery before rendering a final review. The central object is the ReviewState, not raw generated prose.

At a high level, the pipeline starts from paper text, extracts paper claims, grounds and binds evidence to those claims, forms reviewer issue candidates, verifies review issue bundles, applies final-view validation, performs non-destructive recovery when needed, and renders the final report from the audited view. The central design decision is to keep direct quote-grounded negative evidence separate from obligation-grounded review issues. A direct quote-grounded negative must be a copied paper quote that itself supports a reviewer-negative relation. An obligation-grounded review issue may instead be verified from a claim anchor, observed paper inventory, a concrete missing or mismatched entity, and the absence of resolving counterevidence.

Operationally, DrMAS is a sequence of typed state transitions rather than a single generation call:

```text
Input: paper text P
1. Extract paper claims C and evidence obligations.
2. Ground support evidence and neutral paper inventory E against P.
3. Form reviewer issue candidates F without treating candidates as evidence.
4. Verify direct quote-grounded negatives and obligation-grounded issue bundles in separate lanes.
5. Build the final-view validation audit H and remove stale, generic, or unsafe critical records.
6. If a supported claim is contested by a verified issue, add a non-destructive contested relation K.
7. Render the final review from the audited state view, not from raw model prose.
```

This algorithmic view is important for the paper's claim. DrMAS does not rely on the model being correct in one pass. Each transition has an explicit evidence requirement, and a failed transition leaves a candidate as diagnosis-pending or rejected rather than allowing it to become a verified flaw.

### 3.2 ReviewState

We define a ReviewState as a structured state object:

```text
S = (C, E, F, G, I, K, R, H)
```

where `C` is the set of extracted paper claims; `E` is the evidence map; `F` is the set of flaw or concern candidates; `G` is the set of evidence gaps and unresolved questions; `I` is the set of verified review issue bundles; `K` is the set of conflict or contested relations; `R` is the recovery-action log; and `H` is the final-view validation audit.

Each claim carries an identifier, text, status, type, importance, coverage tags, and optional claim obligations. Each evidence record carries an identifier, claim binding, quote or inventory text, source locator, stance, strength, grounding labels, semantic labels, and review-negative labels when applicable. The final report is not rendered from raw model output; it is rendered from an audited state view.

### 3.3 Evidence Grounding And Claim Binding

DrMAS first grounds evidence against the paper and binds it to real claims. The evidence map records the target claim, raw quote or evidence text, source locator, source bucket, grounding label, semantic label, stance, strength, binding status, and binding rationale.

The system distinguishes support evidence from negative or missing evidence. Accept-like support requires real-claim binding and verified evidence quality. This prevents fallback claims, parser artifacts, or context-only snippets from becoming accept-level support. This evidence layer also builds neutral paper inventory. Inventory is not treated as negative evidence. It is used later to verify whether a reviewer issue is a real claim-inventory-obligation mismatch.

### 3.4 Two Critical-Content Lanes

DrMAS uses two separate lanes for review-critical information.

![Figure 2: Direct quote-grounded negative lane vs obligation-grounded issue lane](paper_figures/figure2_critical_content_lanes.svg)

Figure 2. DrMAS separates direct quote-grounded reviewer negatives from obligation-grounded review issues. The first lane requires a copied paper quote that itself supports a reviewer-negative relation. The second lane verifies issues from a claim-inventory-obligation mismatch, allowing concerns such as missing ablations or missing baselines to be represented without fabricating negative quotes.

The direct lane is intentionally strict. A record can count as a quote-grounded reviewer negative only if it passes all of the following checks:

```text
paper-grounded quote
AND semantic negative relation
AND reviewer-negative relation
AND real claim binding
AND non-noise negative type
AND linked flaw or issue
```

This lane is counted by `review_negative_verified_count`. The present paper keeps this lane separate from the obligation-grounded issue result and does not claim direct quote-grounded negative recall improvement.

The second lane verifies reviewer issues that are not copied negative quotes. This is the current main mechanism. An obligation-grounded issue is represented as a review issue bundle containing an issue identifier, claim identifier, issue type, required evidence type, claim anchor, observed inventory anchor, missing or mismatched entity, source of expectation, verification status, and an explicit marker that the issue is not a quote-negative record. This lane is counted by `verified_review_issue_count` and deduplicated by `verified_review_issue_cluster_count`.

### 3.5 Review Issue Bundle Verification

The verifier checks whether a candidate review issue is auditable from the paper state. Conceptually, a candidate bundle becomes a verified issue only if:

```text
real_claim
AND locatable_claim_anchor
AND concrete_missing_or_mismatch_entity
AND auditable_expectation
AND verifiable_observed_inventory
AND issue_type_relevant_inventory
AND missing_entity_not_already_observed
AND no_ablation_or_full_text_counterevidence
AND review_worthiness_gate
AND not_author_limitation_or_retrieval_gap
```

Important verifier gates include claim anchor locatability, source-of-expectation checks, concrete missing item checks, missing-baseline specificity, missing-ablation target quality, observed inventory availability and relevance, counterevidence from inventory and full text, review-worthiness checks, and rejection of author self-limitations, generic gaps, and retrieval gaps.

For missing-ablation issues, the target-quality gate is particularly important. Generic targets such as bare "encoder", "decoder", "network", "component", action fragments, or ordinary training actions are rejected or downgraded. Named contribution mechanisms or paper-specific performance-driving components may pass as high or medium confidence.

The verifier is deliberately precision-oriented. A rejected candidate may still be useful as a diagnosis-pending concern, but it is not counted as a verified review issue.

### 3.6 Materializing Verified Issues

When a bundle is verified, DrMAS materializes it as structured state rather than as an unstructured criticism. The materialized record says that the issue is verified by absence or coverage audit, not by a direct negative quote. The final view can then render it as a verified review issue or contested concern without mixing it into `review_negative_verified_count`.

This distinction is important for the paper's safety story. The system can surface a missing-ablation or missing-baseline issue while still refusing to call a neutral experiment table a negative quote. It can also leave a candidate as diagnosis-pending when the missing item, inventory anchor, or counterevidence check is insufficient.

### 3.7 Final-View Validation

The final-view validation pass constructs an audited decision/report view. This view verifies evidence records against the current state, builds evaluation and method inventory, performs claim-requirement audit, materializes verified review issue bundles, filters stale gaps and stale conflicts, reconciles support in the audited view, downgrades unsafe flaws, tracks active negative-grounding conflicts, and deduplicates review issue rows into clusters.

This step prevents false negative-evidence artifacts from leaking into the final review. In the reported artifacts, stale reviewer-absence anchors and quote-bank negative candidates that no longer pass the verifier are treated as safe rejections, not active conflicts.

### 3.8 Recovery As Non-Destructive Repair

Recovery is not a mechanism for forcing accept/reject decisions. It is a mechanism for repairing ReviewState inconsistencies. The preferred recovery action is `mark_contested`: a supported claim can remain supported while being marked contested by a verified review issue.

![Figure 4: Non-destructive recovery](paper_figures/figure4_non_destructive_recovery.svg)

Figure 4. Recovery in DrMAS is non-destructive. Verified review issues can create a supported-but-contested relation rather than downgrading a claim that has real positive support.

This preserves a supported claim while exposing that a verified issue contests its sufficiency or scope. Unsafe downgrade attempts are tracked separately and should not be described as the main recovery path. The paper should describe recovery as:

```text
supported claim + verified issue -> supported-but-contested relation
```

and not as:

```text
verified issue -> downgrade claim status
```

### 3.9 Rendering The Final Review

The final report is rendered from the audited view. This lets the report distinguish strengths supported by real evidence, direct quote-grounded reviewer negatives if any, obligation-grounded verified review issues, diagnosis-pending concerns, assessment limitations, contested claims, and unresolved questions.

This design is essential to the paper narrative. The final review should not collapse all weak signals into a single flaw list. It should preserve the lifecycle state of each concern.

The implementation appendix maps these paper concepts to code anchors, regeneration commands, and artifact identifiers. The main text focuses on the review-state concepts and reports only the identifiers needed to make the empirical claims traceable.

## 4. Experiments

### 4.1 Research Questions

We evaluate DrMAS around four questions that follow from the ReviewState thesis.

RQ1 asks whether the system can verify reviewer issues without relying on copied negative quotes. This tests the obligation-grounded review issue bundle pathway. The expected evidence is not a negative sentence from the paper, but a verified mismatch among a paper claim, observed inventory, and a concrete missing or mismatched entity.

RQ2 asks whether the final view suppresses unsafe negative-evidence artifacts. This tests whether positive statements, author limitations, quote-bank artifacts, retrieval gaps, and stale absence records are prevented from becoming active negative-grounding conflicts.

RQ3 asks whether verified issues can trigger non-destructive recovery. This tests whether supported claims can remain supported while being marked contested by verified review issues, rather than being destructively downgraded.

RQ4 asks what still limits the current system. This covers the remaining gap between a conservative state-verification framework and broad autonomous reviewer issue discovery.

### 4.2 Evaluation Setting

We use a 20-paper hard-negative diagnostic set designed to stress negative-evidence and reviewer-issue handling. The main reported evidence is a two-run clean-repeat result using the current issue-bundle verifier, manual audit protocol, and recovery checks. Both accepted runs complete all 20 papers and pass the machine and manual gates. Exact run identifiers, regeneration commands, and artifact paths are recorded in the reproducibility appendix rather than used as part of the paper's main narrative.

### 4.3 Metrics

We distinguish direct quote-grounded negatives from obligation-grounded review issues.

A direct quote-grounded negative is a paper quote that itself supports a reviewer-negative relation after grounding, semantic, and review-relation verification. This is counted by `review_negative_verified_count`.

An obligation-grounded review issue is a verified issue bundle supported by a real claim anchor, observed inventory anchor, concrete missing or mismatched entity, and a counterevidence check. This is counted by `verified_review_issue_count` and deduplicated by `verified_review_issue_cluster_count`.

We report rows and clusters separately. Rows are individual verified issue records. Clusters deduplicate repeated detections of the same issue target in the same paper. The paper-level headline uses clusters.

Safety and final-view validation metrics include active negative-grounding conflicts, semantic anchor conflicts, semantic negatives without review relation, unlinked negative evidence, and positive/neutral negative candidates. Recovery metrics include mark-contested commits, verified-review-issue repairs, and harmful recovery commits.

### 4.4 Main Result: Verified Review Issue Bundles

Table 1 reports the current clean-repeat diagnostic result. Across two accepted hardneg20 clean runs, DrMAS produces five recurring Critique-origin verified review issue clusters. The recurring clusters are manually judged A/B, have zero manual-D labels, and connect to contested recovery in both runs.

| Metric | Value |
| --- | ---: |
| accepted hardneg20 clean runs | 2 |
| completed papers per run | 20 |
| recurring Critique-origin verified issue clusters | 5 |
| Critique-origin cluster Jaccard mean | 1.000 |
| manual-D total across accepted runs | 0 |
| harmful recovery commits | 0 |
| recurring efficiency-cost-gap clusters | 1 |
| recurring missing-ablation clusters | 2 |
| recurring missing-baseline clusters | 2 |

Table 1. Main hardneg20 clean-repeat result. The headline unit is a recurring Critique-origin cluster, not a raw row count. These recurring clusters are obligation-grounded issue bundles and are not presented as direct quote-grounded negative evidence.

![Figure 3: Verification funnel from rows to clusters to manual A/B clusters](paper_figures/figure3_verification_funnel.svg)

Figure 3. Review issue quality is reported at the cluster level. The paper headline uses recurring Critique-origin clusters across accepted clean runs rather than raw row count from a single run.

The key interpretation is that the useful negative-review signal does not appear as copied paper-negative text. It appears as verified claim-inventory-obligation mismatch. This supports the ReviewState thesis: reviewer issues should be represented as auditable state objects rather than as unstructured negative snippets.

### 4.5 Illustrative Issue Bundle

One verified cluster illustrates the distinction. In the SpecDec++ case, the paper claims an adaptive candidate-length mechanism and states that it uses "a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens." DrMAS treats this statement as neutral inventory evidence: it shows that a named mechanism exists, but it is not itself a negative quote. The verified issue is the missing relation between the claim, the named mechanism, and the expected component-isolation ablation for the acceptance prediction head.

| Bundle element | SpecDec++ acceptance-prediction-head cluster |
| --- | --- |
| Claim anchor | Adaptive candidate length is presented as a mechanism for boosting speculative decoding performance. |
| Observed inventory anchor | The paper states that it augments the draft model with a trained acceptance prediction head. |
| Missing relation | The verified inventory does not show a component-isolation ablation for the acceptance prediction head. |
| Verification status | High-confidence missing-ablation target; one deduplicated issue cluster over three related rows. |
| Recovery action | The supported claim is marked contested by the verified issue rather than downgraded. |

Table 2. Compact audit trail for the illustrative issue bundle. The inventory anchor is neutral paper content, not a negative quote; the review issue comes from the verified claim-inventory-obligation mismatch.

This case is counted as one issue cluster, not as multiple independent defects, even though it appears in three related rows attached to overlapping claims. The target-quality gate classifies the acceptance prediction head as a high-confidence missing-ablation target because it is a named mechanism rather than a generic component. Recovery then applies `mark_contested` to the supported claim: the claim remains supported, but the audited state records that its evidence is contested by a verified review issue. This example is expanded in the case-study appendix.

### 4.6 Manual Cluster Audit

Table 3 summarizes the recurring cluster audit. The audit unit is a deduplicated issue cluster that recurs across accepted clean runs, not a raw row. We use A for clear review-worthy issues and B for defensible reviewer concerns that should be worded cautiously. The five recurring Critique-origin clusters are all A/B and connect to contested recovery in both runs.

| Paper | Issue type | Cluster target | Manual label | Recurrence | Contested recovery |
| --- | --- | --- | --- | ---: | ---: |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | A | 2/2 | 2/2 |
| GE6iywJtsV | missing_ablation | graph_control_module | A/B | 2/2 | 2/2 |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | B | 2/2 | 2/2 |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | A/B | 2/2 | 2/2 |
| YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | B | 2/2 | 2/2 |

Table 3. Recurring Critique-origin obligation-grounded review issue clusters across two accepted hardneg20 clean runs. The table reports deduplicated cluster-level evidence, manual A/B labels, and whether the issue connects to contested recovery in both runs.

The issue distribution is intentionally reported as a limitation: the recurring clusters contain one efficiency-cost gap, two missing-ablation issues, and two missing-baseline issues. This is enough to demonstrate recurring Critique-origin issue-bundle verification, but not enough to claim broad reviewer issue diversity.

### 4.7 Recovery And Safety

Table 4 reports recovery and safety signals for the two accepted clean runs. The main recovery action is `mark_contested`: a supported claim can remain supported while being marked contested by a verified review issue. This is non-destructive state repair, not a decision override.

| Metric | Clean R1 | Clean R3 |
| --- | ---: | ---: |
| completed papers | 20 | 20 |
| machine gate | PASS | PASS |
| manual gate | PASS | PASS |
| manual A/B clusters | 7 | 7 |
| Critique-origin manual A/B clusters | 5 | 5 |
| manual-D clusters | 0 | 0 |
| mark-contested commits | 20 | 16 |
| verified-review-issue repairs | 17 | 14 |
| harmful recovery commits | 0 | 0 |

Table 4. Recovery and safety metrics for the accepted clean runs. Verified issues can expose supported-but-contested claims without destructively downgrading claim status. Harmful recovery remains zero in both runs.

The recurring clusters also exercise the non-destructive recovery path. Each recurring Critique-origin cluster has per-run `mark_contested` support, so the system can keep a supported claim in the state while exposing a verified issue as a contested relation. This supports the ReviewState-maintenance thesis: recovery is reported as auditable state repair, not as accept/reject correction.

### 4.8 Interpretation Of The Diagnostic Result

The diagnostic result should not be read as a simple count-maximization exercise. Earlier development runs produced more issue rows by allowing generic or malformed missing-ablation targets, but those rows were not paper-ready. The current reported result is intentionally smaller because it applies target-quality checks, counterevidence checks, clustering, and final-view conflict cleanup before a concern can be counted as a verified review issue.

This interpretation matters for the paper. The contribution is not that the system maximizes the number of criticisms. The contribution is that it separates candidate generation from conservative issue verification, reports row-level duplicates separately from cluster-level issues, and keeps stale or quote-bank false-negative anchors out of the final view.

## 5. Discussion

The strongest current result is not the number of negative quotes. It is the repeated conversion of Critique-origin reviewer concerns into verified obligation-grounded state objects. This is consistent with the main insight: many useful review concerns are not negative sentences in the paper. They are reviewer-inferred obligation gaps that require structured verification.

Across two accepted clean runs, five Critique-origin issue clusters recur exactly and all five have A/B manual labels with contested-recovery support in both runs. This supports a conservative claim: DrMAS can turn reviewer-style concerns into auditable ReviewState objects and connect those objects to non-destructive recovery.

The result also clarifies what row counts can and cannot mean. A row is an individual verified issue record. A cluster is a deduplicated issue target within a paper. Since repeated detections can attach to overlapping claims, the paper should report recurring cluster count and manual audit rather than raw row count from a single run.

The result is not yet a broad autonomous review benchmark. The recurring issue distribution contains two missing-ablation clusters, two missing-baseline clusters, and one efficiency-cost gap. The appropriate next step is not to loosen the verifier, but to improve entity-level obligation extraction and Critique-driven candidate generation while preserving the same final-view protections.

Responsible use follows from the same framing. DrMAS should be used as review support and audit infrastructure, not as an autonomous reviewer, accept/reject classifier, or source of final review judgments. A human reviewer should be able to inspect whether each concern is a direct quote-grounded negative, an obligation-grounded verified issue, or a diagnosis-pending concern before using it in a review. Any deployment also needs to respect manuscript confidentiality and the target venue's policy on LLM assistance; this paper evaluates state verification and rendering safeguards, not policy compliance.

## 6. Limitations

This experiment has five important limitations.

First, hardneg20 is a diagnostic set. It is useful for stress-testing ReviewState validation and reviewer issue verification, but it is not enough by itself to support broad benchmark claims.

Second, the issue distribution is narrow. The recurring clusters cover two missing-ablation concerns, two missing-baseline concerns, and one efficiency-cost gap. This supports the issue-bundle mechanism, not comprehensive reviewer issue coverage.

Third, the result is a clean-repeat diagnostic, not full39 generalization. Larger-domain evaluation should come after the ReviewState lifecycle and narrative are stable.

Fourth, the paper does not claim accept/reject accuracy improvement, PPO or RL gains, or broad autonomous flaw discovery. DrMAS is evaluated as review support and audit infrastructure.

Fifth, direct quote-grounded negative evidence remains a separate lane. The present result supports obligation-grounded issue verification and contested recovery; it should not be described as direct quote-grounded negative recall improvement.

This evidence is sufficient for a conservative framework paper, but not for a broad benchmark claim. A future full39 evaluation or larger-domain study would strengthen external validity only if it preserves the same verifier, manual-audit, and recovery safeguards.

## 7. Conclusion

LLM-assisted peer review should not be evaluated only as a problem of generating fluent review text. A useful review assistant must track what is supported, contested, speculative, stale, or unsafe to render. DrMAS addresses this by maintaining an explicit ReviewState with claims, evidence, review issues, conflicts, final-view validation diagnostics, and recovery actions.

The current diagnostic results show that obligation-grounded review issues can be verified conservatively through claim anchors, observed inventory, concrete missing or mismatched entities, and counterevidence checks, while measured false-negative-evidence artifacts are kept out of the final view. The direct quote-grounded negative lane remains unsolved in the current run, and broad autonomous issue discovery remains future work.

The main contribution is therefore a stateful verification and recovery framework for LLM-assisted reviewing: a way to make review text accountable to an auditable lifecycle before it reaches the final report.
