# P31.6 Manual Critique-Origin Audit: P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150

- source entry gate: `P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_ENTRY_GATE_AUDIT.json`
- source case table: `P31_9_CRITMENU_AUDIT_FROM_FRESH_20260704_191150_REVIEW_ISSUE_CASE_TABLE.json`
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
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for graph control module
claim_anchor = Diff-Shape is a novel constrained diffusion model for shape-based de novo drug design that uses a Graph ControlNet architecture to condition a pre-trained molecular diffusion model (MIDI) on the 3D shape of a template...
inventory_locator = paper component inventory #1
inventory = This approach allowed ControlNet to learn a diverse range of conditional models.(Zhang et al., 2023) Inspired by ControlNet, we introduce a novel diffusion model called Diff-Shape, which combines a pre-trained uncondi...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 2. GE6iywJtsV / implementation_reproducibility_details

```text
issue_type = reproducibility_gap
origin = deterministic_seed
claim_ids = claim-1
missing = training hyperparameters, configuration, seed, or implementation detail for ControlNet
claim_anchor = Diff-Shape introduces a novel Graph ControlNet architecture to condition a pre-trained molecular diffusion model on 3D shape constraints for de novo drug design.
inventory_locator = Figure 1
inventory = Figure 1: The basic architecture of GrCN, consisting of a constrain module and a 3D generation module.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 3. HPuLU6q7xq / modeling_coarse_and_fine-grained_fusion

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-2
missing = component-isolation ablation for modeling coarse and fine-grained fusion
claim_anchor = The Orca training pipeline uses a four-stage process for data processing and model training.
inventory_locator = paper component inventory #1
inventory = For the coarse-grained model, we train the model by splicing personality trait reports into queries.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 4. NnExMNiTHw / acceptance_prediction_head

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for trained acceptance prediction head
claim_anchor = SpecDec++ is a method that boosts speculative decoding performance by adaptively selecting candidate lengths using a lightweight prediction head.
inventory_locator = paper component inventory #1
inventory = We augment the draft model with a trained acceptance prediction head to predict the conditional acceptance probability of the candidate tokens.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 5. QAgwFiIY4p / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-2
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The Point Set Transformer (PST) is efficient and performs strongly in learning graph representations.
inventory_locator = paper inventory #2
inventory = Extensive experiments further validate PST's outstanding real-world performance.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 6. QAgwFiIY4p / implementation_reproducibility_details

```text
issue_type = reproducibility_gap
origin = deterministic_seed
claim_ids = claim-1
missing = training hyperparameters, configuration, seed, or implementation detail for PSRD
claim_anchor = The paper introduces a bijective graph-to-point-set conversion method (PSRD coordinates) that transforms interconnected nodes into a set of independent points for use with set encoders.
inventory_locator = Section: Experiments
inventory = Moreover, our graph-to-set method is adaptable to various configurations.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 7. WNxlJJIEVj / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-2
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = CDiffuser demonstrates performance advantages (improved efficiency/policy performance) in offline RL tasks with large ratios of low-return trajectories.
inventory_locator = paper inventory #1
inventory = The performance of offline reinforcement learning (RL) is sensitive to the proportion of high-return trajectories in the offline dataset.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 8. WpXq5n8yLb / recurrent_draft_model

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for recurrent neural network
claim_anchor = ReDrafter is an advanced speculative decoding approach that achieves state-of-the-art speedup for LLM inference.
inventory_locator = paper component inventory #1
inventory = Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 9. WpXq5n8yLb / gpt-4_chatgpt_llama-family_baseline_under_the_same_benchmark

```text
issue_type = missing_baseline
origin = deterministic_seed
claim_ids = claim-1
missing = GPT-4/ChatGPT/Llama-family baseline under the same benchmark
claim_anchor = ReDrafter achieves state-of-the-art speedup (up to 3.5x on Vicuna for MT-Bench) for LLM inference.
inventory_locator = paper inventory #1
inventory = We present Recurrent Drafter (ReDrafter), an advanced speculative decoding approach that achieves state-of-the-art speedup for large language models (LLMs) inference.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 10. XH3OiIhtvf / incorporating a secure aggregator in the federated model results in a less favor

```text
issue_type = direct_contradiction
origin = quote_grounded
claim_ids = claim-2
missing = 
claim_anchor = The secure aggregator integrates diverse local models into a single global model that improves overall performance.
inventory_locator = comparison/Section 4.3
inventory = incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 11. XH3OiIhtvf / incorporating a secure aggregator in the federated model results in a less favor

```text
issue_type = negative_result
origin = quote_grounded
claim_ids = claim-3
missing = 
claim_anchor = The proposed method achieves an 8.57% improvement in performance compared to a baseline.
inventory_locator = Table 1
inventory = incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 12. YXn76HMetm / equalal_baseline

```text
issue_type = missing_baseline
origin = deterministic_seed
claim_ids = claim-3
missing = same-setting comparison against paper-named EqualAL baseline
claim_anchor = HALO outperforms the RIPU baseline by +2.9% mIoU with a 5% labeling budget on a novel dataset.
inventory_locator = paper inventory #3
inventory = HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that surpasses the performance of supervised domain adaptation while using ...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 13. a6SntIisgg / global_encoder

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-logora-uses-a-novel-local-global
missing = component-isolation ablation for Global Encoder
claim_anchor = LogoRA uses a novel local-global representation alignment framework for unsupervised domain adaptation of time series.
inventory_locator = paper component inventory #1
inventory = To address this issue, we propose the \textbf{Lo}cal-\textbf{G}l\textbf{o}bal \textbf{R}epresentation \textbf{A}lignment framework (\abbr), which employs a two-branch encoder—comprising a multi-scale convolutional bra...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 14. fGXyvmWpw6 / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = deterministic_seed
claim_ids = claim-3
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The method is computationally efficient, requiring only a few hundred local distillation steps using feature distributions, and is more efficient than other bi-level dataset distillation approaches.
inventory_locator = paper inventory #1
inventory = Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when training on heterogeneous data.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 15. mHv6wcBb0z / generalized_noise_regularization

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for with a generalized noise regularization
claim_anchor = The paper proposes NR-DCCA, a method that incorporates noise regularization to prevent model collapse in DCCA.
inventory_locator = paper component inventory #1
inventory = Therefore, this paper develops NR-DCCA, a DCCA-based method equipped with a generalized noise regularization (NR) approach.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 16. ye3NrNrYOY / loss

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-2
missing = component-isolation ablation for E loss
claim_anchor = The TCMT method uses a latent causal variable model to capture and transfer temporal causal mechanisms, with an encoder and classifier network that are updated during adaptation.
inventory_locator = paper component inventory #1
inventory = Our overall loss function for action recognition combines the classification loss and evidence lower bound (ELBO): $$ \mathcal{L}=\mathcal{L}_{\mathrm{ELBO}}+\mathcal{L}_{\mathrm{cls}} $$ The ELBO loss combines the re...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO
