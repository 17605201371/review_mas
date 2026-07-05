# P31.6 Manual Critique-Origin Audit: P32_CLEAN_R1_20260705_232527

- source entry gate: `P32_CLEAN_R1_20260705_232527_ENTRY_GATE_AUDIT.json`
- source case table: `P32_CLEAN_R1_20260705_232527_REVIEW_ISSUE_CASE_TABLE.json`
- audit date: ``
- status: **TODO**

## Rubric

- `A`: clear review-worthy issue with strong claim/inventory/missing relation
- `B`: defensible review concern; usable with careful wording
- `C`: weak or over-specific concern; keep only as diagnosis/pending
- `D`: false positive / contradicted by paper text
- `MERGE`: duplicate of another audited cluster; do not count separately

## Clusters To Audit

### 1. 9zEBK3E9bX / sz-softmax_loss

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for sz-Softmax loss
claim_anchor = SPOT is a label-efficient pre-training method for 3D perception.
inventory_locator = paper component inventory #1
inventory = Finally, we use class-balancing cross entropy loss and Lova´sz-Softmax loss to guide the pre-training.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 2. GE6iywJtsV / graph_control_module

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-3
missing = graph control module; component-isolation ablation for with a graph control module
claim_anchor = The paper introduces a novel constrained diffusion model (Diff-Shape) and a Graph ControllNet (GrCN) for shape-based de novo drug design.
inventory_locator = Section 3.2
inventory = In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it composed an unconditioned diffusion model satisfying SE (3) symmetry for 3D molecular generation a
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 3. GE6iywJtsV / et al., 2004) in our study, we utilized an unconditioned midi model as the basel

```text
issue_type = insufficient_evaluation
origin = quote_grounded
claim_ids = claim-2
missing =
claim_anchor = Diff-Shape outperforms baseline methods in generating molecules with high shape similarity to a reference while maintaining novel chemical structures, as demonstrated by quantitative metrics like Tanimoto similarity, ...
inventory_locator = Comparison / Robustness excerpt #2
inventory = et al., 2004) In our study, we utilized an unconditioned MIDI model as the baseline. We conducted a performance comparison between Diff-Shape and two other shape-conditioned generative models: SQUID and ShapeMol. The $\l
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 4. HPuLU6q7xq / modeling_coarse_and_fine-grained_fusion

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-3
missing = component-isolation ablation for modeling coarse and fine-grained fusion
claim_anchor = The method involves a multi-stage process, including personality traits inferring, training data generation, and model fine-tuning.
inventory_locator = paper component inventory #1
inventory = For the coarse-grained model, we train the model by splicing personality trait reports into queries.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 5. HPuLU6q7xq / paper-named_gpt-4_baseline

```text
issue_type = missing_baseline
origin = critique_payload
claim_ids = claim-2
missing = same-setting comparison against paper-named GPT-4 baseline
claim_anchor = The Orca method empirically outperforms baseline methods on role-playing tasks.
inventory_locator = Table/Figure excerpt #2
inventory = \caption{An example interaction between an personalized agent object of Orca and human on social platform.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 6. NnExMNiTHw / acceptance_prediction_head

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-2, claim-4
missing = acceptance prediction head; component-isolation ablation for of the acceptance prediction head
claim_anchor = SpecDec++ formulates the candidate length selection as an MDP and implements an adaptive policy to choose K.
inventory_locator = Section: SpecDec++: Theory and Algorithm
inventory = Theory and Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \caption{\ours uses a trained \textbf{acceptance prediction hea
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 7. QAgwFiIY4p / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = claim_obligation
claim_ids = claim-2, claim-3
missing = parameters measurement under the claimed setting
claim_anchor = The proposed method achieves competitive or superior performance on graph tasks (e.g., classification, regression) while using fewer parameters than baseline GNNs.
inventory_locator = Table/Figure caption: Results on graph property prediction tasks.
inventory = \caption{Results on graph property prediction tasks.}\label{tab::zinc}
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 8. QAgwFiIY4p / held-out_coverage_for_parameter-efficient

```text
issue_type = missing_robustness_or_generalization
origin = deterministic_seed
claim_ids = claim-3
missing = held-out or coverage evaluation for parameter-efficient
claim_anchor = The proposed PST method achieves competitive or superior performance on various graph tasks while being more parameter-efficient compared to existing GNNs and transformers.
inventory_locator = Table/Figure caption: Results on graph property prediction tasks.
inventory = \caption{Results on graph property prediction tasks.}\label{tab::zinc}
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 9. WpXq5n8yLb / recurrent_draft_model

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2, claim-3
missing = component-isolation ablation for recurrent neural network
claim_anchor = ReDrafter leverages a recurrent neural network (RNN) as the draft model conditioning on the LLM's hidden states.
inventory_locator = paper component inventory #1
inventory = Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 10. XH3OiIhtvf / incorporating a secure aggregator in the federated model results in a less favor

```text
issue_type = negative_result
origin = quote_grounded
claim_ids = claim-4
missing =
claim_anchor = Using the secure aggregator does not significantly harm performance compared to not using it.
inventory_locator = Figure 2
inventory = However, it is important to note that incorporating a secure aggregator in the federated model results in a less favorable outcome than the baseline system, as indicated in the table.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 11. XyB4VvF01X / graph2tac_learns_hierarchical_representation_module

```text
issue_type = missing_ablation
origin = claim_obligation
claim_ids = claim-1
missing = ablation isolating Graph2Tac learns a hierarchical representation module
claim_anchor = Graph2Tac learns a hierarchical representation of math concepts from their graph structure to aid theorem proving.
inventory_locator = paper component inventory #1
inventory = ![](images/762a4f125e2fd75a49cfa72e5afdff9e3580c2ccde897fcc71210541d29cb604.jpg) Figure 3: Our novel definition training task is trained to calculate hierarchical representations for new definitions that may in turn b...
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 12. YXn76HMetm / paper-named_pixelpick_baseline

```text
issue_type = missing_baseline
origin = critique_payload
claim_ids = claim-3
missing = same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL baseline
claim_anchor = The HALO method empirically outperforms baseline methods (including EqualAL) for active learning semantic segmentation under domain shift.
inventory_locator = Comparison / Robustness excerpt #1
inventory = HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that surpasses the performance of supervised domain adaptation while using onl
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 13. YXn76HMetm / held-out_coverage_for_equalal

```text
issue_type = missing_robustness_or_generalization
origin = deterministic_seed
claim_ids = claim-3
missing = held-out or coverage evaluation for EqualAL
claim_anchor = HALO achieves state-of-the-art performance and improves over baselines like EqualAL under domain shift.
inventory_locator = Comparison / Robustness excerpt #1
inventory = HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first active learning approach that surpasses the performance of supervised domain adaptation while using onl
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 14. a6SntIisgg / architecture_global_encoder

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for architecture of Global Encoder
claim_anchor = LogoRA proposes a novel local-global representation alignment framework using a two-branch encoder (multi-scale convolutional and Transformer) to capture both local and global features.
inventory_locator = paper component inventory #1
inventory = Considering the network architecture, we employ a two-branch encoder, using a multi-scale convolutional branch and a patching transformer branch.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 15. a6SntIisgg / held-out_coverage_for_source-to-target

```text
issue_type = scope_overclaim
origin = critique_payload
claim_ids = claim-3
missing = held-out or coverage evaluation for source-to-target
claim_anchor = LogoRA achieves the best accuracy compared to baseline methods.
inventory_locator = Figure: model
inventory = The complete \abbr framework for unsupervised domain adaptation is illustrated in \figurename~\ref{fig:model}. It primarily comprises four modules: a feature extractor denoted as $F(\cdot)$, a fusion module denoted as $G
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 16. fGXyvmWpw6 / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = critique_payload
claim_ids = claim-1, claim-4
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = The proposed method is computationally efficient, reducing communication rounds and training time compared to other methods.
inventory_locator = paper inventory #1
inventory = Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible to performance drops when training on heterogeneous data.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 17. mHv6wcBb0z / noise_perform_specific_regularization

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1
missing = component-isolation ablation for of noise perform specific regularization
claim_anchor = The paper proposes NR-DCCA, a method using noise regularization to prevent model collapse in DCCA.
inventory_locator = Section: Method
inventory = \subsection{Method} Based on the discussions in previous sections, we present NR-DCCA, which makes use of the noise regularization approach to prevent model collapse in DCCA.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO
