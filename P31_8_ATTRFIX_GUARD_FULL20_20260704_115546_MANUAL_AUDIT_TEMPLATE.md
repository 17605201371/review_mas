# P31.6 Manual Critique-Origin Audit: P31_8_ATTRFIX_GUARD_FULL20_20260704_115546

- source entry gate: `P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_ENTRY_GATE_AUDIT.json`
- audit date: ``
- status: **TODO**

## Rubric

- `A`: clear review-worthy issue with strong claim/inventory/missing relation
- `B`: defensible review concern; usable with careful wording
- `C`: weak or over-specific concern; keep only as diagnosis/pending
- `D`: false positive / contradicted by paper text
- `MERGE`: duplicate of another audited cluster; do not count separately

## Clusters To Audit

### 1. GE6iywJtsV / graph_control_module

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-2, claim-4
missing = component-isolation ablation for graph control module
claim_anchor = Diff-Shape is built upon the Graph ControllNet (GrCN) architecture, which combines an unconditioned diffusion model (MIDI) with a graph control module for 3D shape conditioning.
inventory_locator = paper component inventory #1
inventory = This approach allowed ControlNet to learn a diverse range of conditional models.(Zhang et al., 2023) Inspired by ControlNet, we introduce a novel diffusion model called Diff-Shape, which combines a pre-trained uncondi...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 2. NnExMNiTHw / acceptance_prediction_head

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-2
missing = component-isolation ablation for train an acceptance prediction head
claim_anchor = SpecDec++ proposes an adaptive candidate length mechanism for speculative decoding, where the number of candidate tokens generated per speculation round is dynamically adjusted based on a learned acceptance probabilit...
inventory_locator = paper component inventory #1
inventory = We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 3. WpXq5n8yLb / recurrent_draft_model

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1
missing = component-isolation ablation for recurrent neural network
claim_anchor = ReDrafter is an advanced speculative decoding approach that achieves state-of-the-art speedup for LLM inference.
inventory_locator = paper component inventory #1
inventory = Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 4. a6SntIisgg / global_encoder

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1
missing = component-isolation ablation for Global Encoder
claim_anchor = LogoRA is a novel local-global representation alignment framework for robust unsupervised domain adaptation (UDA) of time series.
inventory_locator = paper component inventory #1
inventory = To address this issue, we propose the \textbf{Lo}cal-\textbf{G}l\textbf{o}bal \textbf{R}epresentation \textbf{A}lignment framework (\abbr), which employs a two-branch encoder—comprising a multi-scale convolutional bra...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 5. fGXyvmWpw6 / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = critique_payload
claim_ids = claim-1, claim-2, claim-3
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The method is computationally efficient, requiring only a few hundred local distillation steps, and is more efficient than other bi-level dataset distillation methods.
inventory_locator = paper inventory #1
inventory = Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when training on heterogeneous data.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 6. mHv6wcBb0z / generalized_noise_regularization

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-2
missing = component-isolation ablation for with a generalized noise regularization
claim_anchor = The proposed NR-DCCA method introduces a noise regularization mechanism to prevent model collapse in DCCA.
inventory_locator = paper component inventory #1
inventory = Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO
