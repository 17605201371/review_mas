# P31.6 Manual Critique-Origin Audit: P31_6_FRESH_20260703_231747

- source entry gate: `P31_6_FRESH_20260703_231747_ENTRY_GATE_AUDIT.json`
- source case table: `P31_6_FRESH_20260703_231747_REVIEW_ISSUE_CASE_TABLE.json`
- audit date: ``
- status: **TODO**

## Rubric

- `A`: clear review-worthy issue with strong claim/inventory/missing relation
- `B`: defensible review concern; usable with careful wording
- `C`: weak or over-specific concern; keep only as diagnosis/pending
- `D`: false positive / contradicted by paper text
- `MERGE`: duplicate of another audited cluster; do not count separately

## Clusters To Audit

### 1. 9zEBK3E9bX / unified_scene_representation

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for unified 3D scene representation
claim_anchor = SPOT is a scalable 3D pre-training method that uses occupancy prediction to learn transferable representations for autonomous driving.
inventory_locator = paper component inventory #1
inventory = In this paper, SPOT is proposed to use 3D semantic occupancy prediction to learn a unified 3D scene representation for various downstream tasks including 3D object detection and LiDAR semantic segmentation.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 2. NnExMNiTHw / acceptance_prediction_head

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for of our trained prediction head
claim_anchor = The paper formulates the choice of the candidate length hyperparameter K in speculative decoding as a Markov Decision Process (MDP).
inventory_locator = paper component inventory #1
inventory = We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 3. QAgwFiIY4p / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-3
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The proposed graph-to-set method is adaptable to various configurations and uses fewer or comparable parameters than baseline models across all datasets.
inventory_locator = paper inventory #2
inventory = Extensive experiments further validate PST's outstanding real-world performance.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 4. WpXq5n8yLb / recurrent_draft_model

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for recurrent neural network
claim_anchor = ReDrafter achieves state-of-the-art speedup for LLM inference as an advanced speculative decoding approach.
inventory_locator = paper component inventory #1
inventory = Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 5. XyB4VvF01X / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-2
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The paper introduces a method (G2T-Anon-Update) for updating model parameters based on new mathematical definitions.
inventory_locator = Comparison / Robustness excerpt #1
inventory = Proof State Text-based Transformer We implement a decoder-only transformer baseline that operates on the textual representations of the proof states, and predicts a textual representation of the tactic.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 6. YXn76HMetm / equalal_baseline

```text
issue_type = missing_baseline
origin = deterministic_seed
claim_ids = claim-2
missing = same-setting comparison against paper-named EqualAL baseline
claim_anchor = The proposed method, HALO, improves over the RIPU baseline by +2.9% mIoU with a 5% budget.
inventory_locator = paper inventory #3
inventory = HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that surpasses the performance of supervised domain adaptation while using ...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 7. YXn76HMetm / held-out_coverage_for_pixel-level

```text
issue_type = missing_robustness_or_generalization
origin = deterministic_seed
claim_ids = claim-2
missing = held-out or coverage evaluation for pixel-level
claim_anchor = HALO outperforms baselines like RIPU in pixel-level active learning for semantic segmentation under domain shift.
inventory_locator = Table: results table
inventory = The ADA performances in Table \ref{tab:results_table} are also compared with the corresponding supervised domain adaptation baselines (Supervised DA).
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 8. a6SntIisgg / global_encoder

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for Global Encoder
claim_anchor = LogoRA proposes a Local-Global Representation Alignment framework for robust unsupervised domain adaptation (UDA) of time series.
inventory_locator = paper component inventory #1
inventory = To address this issue, we propose the \textbf{Lo}cal-\textbf{G}l\textbf{o}bal \textbf{R}epresentation \textbf{A}lignment framework (\abbr), which employs a two-branch encoder—comprising a multi-scale convolutional bra...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 9. fGXyvmWpw6 / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-2, claim-3
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The method is computationally efficient, requiring only a few hundred local distillation steps, and is more efficient than other bi-level dataset distillation approaches.
inventory_locator = paper inventory #1
inventory = Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when training on heterogeneous data.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 10. mHv6wcBb0z / generalized_noise_regularization

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for with a generalized noise regularization
claim_anchor = The paper proposes a new method called NR-DCCA to prevent model collapse in Deep Canonical Correlation Analysis (DCCA) by applying noise regularization.
inventory_locator = paper component inventory #1
inventory = Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 11. ye3NrNrYOY / domain_causal_representation

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for domain of causal representation
claim_anchor = The paper proposes Temporal Causal Mechanism Transfer (TCMT), a new framework for few-shot action recognition.
inventory_locator = paper component inventory #1
inventory = Our experimental evaluations across standard action recognition datasets validate our hypothesis that our proposed method of Temporal Causal Mechanism Transfer (TCMT) enables efficient few-shot action recognition in v...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO
