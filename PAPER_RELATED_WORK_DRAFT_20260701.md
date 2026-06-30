# Related Work Draft

Date: 2026-07-01

This draft positions DrMAS around ReviewState maintenance, not broad autonomous review generation. Citation placeholders are intentionally explicit. Do not convert them into final references until the exact bibliography is checked.

## 2. Related Work

### 2.1 LLM-Assisted Peer Review

Recent work studies whether large language models can provide useful feedback on research papers, summarize manuscripts, identify weaknesses, or assist reviewers during peer review [TODO: cite LLM peer-review evaluation papers]. These systems often evaluate generated review text directly: whether it is helpful, whether it overlaps with human reviews, or whether authors and reviewers perceive it as useful.

DrMAS addresses a complementary problem. Instead of treating review generation as the main object, it treats the intermediate review state as the object that must be maintained, audited, and repaired. This distinction matters because a fluent review can mix grounded strengths, unsupported criticisms, author-stated limitations, retrieval failures, and speculative concerns in the same prose. DrMAS therefore represents claims, evidence, reviewer issues, conflicts, and recovery actions as structured state before rendering the final review.

The current results should not be framed as showing that DrMAS is a better general review generator. The evidence supports a narrower claim: DrMAS can verify obligation-grounded review issue bundles and suppress measured false-negative-evidence artifacts on a diagnostic hard-negative set.

Citation targets:

- LLMs for scientific peer review and paper feedback.
- Human evaluation of LLM-generated reviews.
- Benchmarks comparing generated reviews with expert reviews.

### 2.2 Retrieval-Augmented And Grounded Scientific Assistance

Retrieval-augmented generation and grounded scientific QA systems aim to reduce hallucination by conditioning generation on source documents and requiring evidence citations [TODO: cite RAG and scientific QA/grounded generation work]. In paper-review settings, this usually means retrieving relevant excerpts and asking the model to justify its comments with quotations or citations.

DrMAS uses grounding, but the central contribution is not retrieval alone. The system distinguishes paper quotes that directly support a claim from neutral inventory anchors that support an absence-style review issue. For example, an experiment table can be positive or neutral paper content while still serving as the observed inventory anchor for a missing-ablation concern. This lets DrMAS verify reviewer issues that are not directly expressed as negative paper sentences.

This is a key difference from a pure quote-grounding view. If a system requires every criticism to be backed by a copied negative quote, it will miss many real reviewer issues. If it relaxes quote requirements without state checks, it risks fabricating defects. DrMAS instead verifies a claim-inventory-obligation mismatch as a structured bundle.

Citation targets:

- Retrieval-augmented generation.
- Citation-grounded generation.
- Scientific claim verification or evidence-grounded scientific QA.
- Document-grounded summarization with citation support.

### 2.3 Factuality, Attribution, And Evidence Verification

A large body of work studies factuality, attribution, and evidence verification for generated text [TODO: cite factuality, attribution, entailment, and citation-verification papers]. These methods ask whether generated statements are supported by source material, whether citations are faithful, or whether an answer contradicts evidence.

DrMAS inherits the same concern but applies it to the lifecycle of a review. The unit of verification is not only a generated sentence. It can be a state object: a claim binding, an evidence record, a review issue bundle, a contested relation, or a recovery patch. This state-level view makes it possible to ask more specific questions:

- Is this evidence grounded in the paper?
- Does it support a real claim or a fallback/context artifact?
- Is a negative label semantically appropriate?
- Is a reviewer issue a direct quote-grounded negative or an obligation-grounded absence issue?
- Is the final report using stale or unlinked evidence?

The P28.6 hygiene metrics are examples of this state-level verification: active negative-grounding conflicts, semantic anchor conflicts, semantic negatives without review relation, unlinked negative evidence, and positive/neutral negative candidates are tracked explicitly.

Citation targets:

- Factual consistency and attribution metrics.
- Citation faithfulness.
- Natural language inference for evidence support.
- Verification of generated scientific claims.

### 2.4 Multi-Agent Reviewing And Self-Correction

Agentic LLM systems often divide a task among roles, such as planner, retriever, verifier, critic, and editor [TODO: cite multi-agent LLM and self-correction work]. Self-correction systems ask models to critique and revise their own outputs, sometimes with tool use or external feedback [TODO: cite Reflexion/Self-Refine-style work after bibliography check].

DrMAS uses multiple roles, but the paper should not frame the contribution as "more agents." The contribution is the persistent ReviewState that agents read and update. Without explicit state semantics, a critic can produce plausible objections that are not grounded, and a repair step can overwrite useful support while trying to fix a flaw. DrMAS constrains repair through typed operations such as `mark_contested`, preserving supported claims while exposing verified issues.

This also explains why recovery is reported as state repair, not decision correction. The current system does not claim to fix accept/reject decisions. It exposes supported-but-contested claims, blocks unsafe downgrade behavior, and records repair attempts in the state.

Citation targets:

- Multi-agent LLM systems.
- LLM self-correction and reflection.
- Tool-using LLM agents.
- Critique-and-revision pipelines.

### 2.5 Review-State And Argument-State Representations

Structured argumentation and evidence graphs represent claims, supports, attacks, and relations among evidence [TODO: cite argument mining, evidence graphs, and claim verification work]. These lines of work are relevant because peer review is not just text generation; it is an argument about a paper's claims, evidence, limitations, and unresolved risks.

DrMAS can be positioned as a review-specific state representation. A ReviewState includes paper claims, evidence records, issue bundles, conflict relations, recovery logs, and final-view hygiene diagnostics. The review issue bundle is especially important: it represents a reviewer concern as a typed relation among a claim anchor, observed inventory, a missing or mismatched entity, and counterevidence checks.

This differs from ordinary argument mining because the state is operational. The system uses the state to decide whether evidence can count, whether a concern should be verified or remain diagnosis-pending, whether a claim should be marked contested, and whether the final report is allowed to render a flaw.

Citation targets:

- Argument mining and argument graphs.
- Claim-evidence relation extraction.
- Evidence-based scientific argumentation.
- Structured review or decision-support systems.

### 2.6 Positioning Summary

DrMAS sits at the intersection of LLM-assisted reviewing, grounded generation, factuality verification, and agentic self-correction. Its distinguishing claim is that reviewing should be treated as auditable state maintenance. The final review should not be trusted merely because it is fluent or quote-rich. It should be trusted only insofar as its claims, evidence, reviewer issues, conflicts, and repairs survive explicit state-level checks.

The current empirical evidence supports this positioning conservatively. P28.6 does not solve direct quote-grounded negative discovery and does not establish broad autonomous issue discovery. It does show that obligation-grounded review issues can be verified as state objects and that measured false-negative-evidence failure modes can be kept out of the final view.

## Drop-In Related Work Summary

Prior work on LLM-assisted peer review focuses on generating or evaluating review text, while work on retrieval-augmented and grounded generation focuses on tying outputs to source documents. DrMAS is complementary: it treats peer review as a state-maintenance problem. The system represents claims, evidence, reviewer issues, conflicts, and recovery actions as typed state objects, then renders the final review from an audited view. This enables a distinction that pure quote-grounding misses: direct quote-grounded negative evidence is different from obligation-grounded reviewer issues such as missing ablations, missing baselines, or reproducibility gaps. DrMAS also differs from generic agentic self-correction by constraining repair through explicit state operations, especially non-destructive contested relations. The current result is therefore best understood as conservative ReviewState verification and recovery, not broad autonomous flaw discovery.

## Citation Checklist

Before final manuscript writing, verify exact references for:

1. LLM-generated peer review and scientific feedback.
2. Retrieval-augmented generation and grounded generation.
3. Citation faithfulness, attribution, and factuality verification.
4. Scientific claim verification and evidence support.
5. Multi-agent LLM systems and self-correction.
6. Argument mining, claim-evidence graphs, and structured decision support.

Do not use invented citation metadata. If a citation cannot be verified, keep the claim category-level or remove it.
