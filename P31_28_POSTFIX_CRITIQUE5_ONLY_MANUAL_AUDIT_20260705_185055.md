# P31.28 Manual Critique-Origin Audit: P31_28_POSTFIX_CRITIQUE5_20260705_185055

- source entry gate: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_ENTRY_GATE_AUDIT.json`
- source case table: `P31_28_POSTFIX_CRITIQUE5_20260705_185055_REVIEW_ISSUE_CASE_TABLE.json`
- audit date: `2026-07-05`
- status: **PASS**

## Summary

- `critique_origin_clusters` = 4
- `manual_A_clusters` = 1
- `manual_B_clusters` = 2
- `manual_A_B_clusters` = 3
- `manual_C_clusters` = 1
- `manual_D_clusters` = 0
- `unfilled_clusters` = 0
- `critique_origin_manual_A_B_clusters` = 3

## Cluster Labels

### 1. GE6iywJtsV / graph_control_module — A

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1
missing = graph control module
claim_anchor = Diff-Shape introduces a novel constrained diffusion model that integrates a Graph Convolutional Network (GrCN) to condition generation on 3D shape constraints for de novo drug design.
inventory_locator = paper component inventory #1
inventory = This approach allowed ControlNet to learn a diverse range of conditional models.(Zhang et al., 2023) Inspired by ControlNet, we introduce a novel diffusion model called Diff-Shape, which combines a pre-trained uncondi...
```

Decision: Keep as paper-facing Critique-origin issue.

Raw paper evidence checked: Paper text repeatedly defines Diff-Shape/GrCN as using a zero-weighted graph control module for shape-conditioned 3D molecular generation.

Counterevidence checked: Searches for ablation/without graph/without Graph Control in the paper text found no component-isolation ablation for the graph control module.

Paper-facing usable: yes

Wording caution: Phrase as missing component-isolation ablation for the Graph ControlNet/graph control module, not as direct negative evidence.

Rationale: Central method component is locatable in the paper and tied to the main constrained-generation claim; no paper-text counterevidence showed an ablation isolating that component.

### 2. NnExMNiTHw / acceptance_prediction_head — B

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-2
missing = our trained prediction head; component-isolation ablation for of the acceptance prediction head
claim_anchor = The paper formulates the choice of candidate length K as a Markov Decision Process (MDP).
inventory_locator = paper component inventory #1
inventory = We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens.
```

Decision: Keep as defensible paper-facing concern with cautious wording.

Raw paper evidence checked: Paper text states SpecDec++ augments the draft model with a trained acceptance prediction head and attributes adaptive candidate length performance to it.

Counterevidence checked: Searches for ablation/without acceptance/prediction-head ablation found no component-isolation ablation for the trained acceptance prediction head.

Paper-facing usable: yes, with caution

Wording caution: Tie the concern to empirical attribution of adaptive decoding gains; do not imply the theoretical MDP/threshold proof itself requires an ablation.

Rationale: The trained prediction head is a concrete method component and no ablation was found, but the cluster spans MDP/theory claims, so it is best framed as an attribution/evaluation concern rather than a flaw in the theory.

### 3. QAgwFiIY4p / coordinates_without_information_loss — C

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1
missing = y coordinates without information loss
claim_anchor = The paper introduces a novel graph-to-set conversion method (PSRD) that bijectively transforms interconnected nodes into a set of independent points using coordinates derived from the Laplacian matrix, and then uses a...
inventory_locator = paper component inventory #1
inventory = Secondly, for Transformer, a specific set encoder, we provide a novel and principled approach to inj
```

Decision: Do not use as paper-facing Stage 2 success; keep only as diagnosis of over-specific target extraction.

Raw paper evidence checked: Paper text contains the phrase that interlinked nodes are transformed into independent points and supplementary coordinates without information loss, supported nearby by SRD/PSRD theorem statements.

Counterevidence checked: Searches found theory/theorem support for the lossless coordinate claim and only unrelated ablation mentions from prior Graph Transformer discussion; no direct empirical ablation target is clearly defined.

Paper-facing usable: no

Wording caution: If discussed, reframe as a possible need for empirical sensitivity analysis of coordinate parameterization, not a missing ablation of “coordinates without information loss”.

Downgrade reason: Target is an over-specific/property phrase rather than a clean component or baseline; the claim is primarily theoretical and has theorem-style support.

Rationale: The paper-grounded phrase is real, but the selected missing-ablation target is not a natural component-level obligation. This is weak diagnostic evidence, not a paper-ready verified Critique discovery.

### 4. YXn76HMetm / equalal_baseline — B

```text
issue_type = missing_baseline
origin = critique_payload
claim_ids = claim-3
missing = same-setting comparison against paper-named EqualAL baseline
claim_anchor = The paper performs a fair empirical comparison of HALO against baselines like EqualAL, demonstrating its effectiveness.
inventory_locator = Table: results table
inventory = approach on a novel dataset, as shown in Table \ref{tab:results_table}c. \subsection{Ablation study} \label{sec:ablation} \input{tables/ablation_tables} We begin by conducting an oracular study using ground-truth labels,
```

Decision: Keep as defensible paper-facing concern with same-setting caveat.

Raw paper evidence checked: Paper text names EqualAL in related active-learning semantic-segmentation work and later claims broad SOTA comparisons for HALO on GTAV/SYNTHIA/ACDC active/domain-adaptation settings.

Counterevidence checked: Searches found EqualAL only in related work; result/comparison windows mention RIPU, D2ADA, Labor/PixelPick context and supervised DA but no EqualAL result table comparison.

Paper-facing usable: yes, with caution

Wording caution: Say the paper omits an EqualAL-style active-learning segmentation comparison or adaptation, rather than asserting EqualAL is definitely same-protocol ADA SOTA.

Rationale: EqualAL is paper-named and relevant to AL segmentation, while the empirical comparison section appears not to include it. The concern is defensible but protocol comparability needs careful wording.
