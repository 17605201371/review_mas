# P31.6 Manual Critique-Origin Audit: P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000

- source entry gate: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000_ENTRY_GATE_AUDIT.json`
- source case table: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000_REVIEW_ISSUE_CASE_TABLE.json`
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
claim_ids = claim-1, claim-2
missing = graph control module; component-isolation ablation for with a graph control module
claim_anchor = Diff-Shape introduces a novel constrained diffusion model for shape-based de novo drug design.
inventory_locator = Claim-matched evidence excerpt #1
inventory = In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and it composed an unconditioned diffusion model satisfying SE (3) symmetry for 3D molecular generation a
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 2. HPuLU6q7xq / modeling_coarse_and_fine-grained_fusion

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2
missing = component-isolation ablation for modeling coarse and fine-grained fusion
claim_anchor = The paper proposes Orca, a novel framework for processing data and training LLMs with custom characters by integrating personality traits, addressing a gap in previous work that focused only on character profiles.
inventory_locator = paper component inventory #1
inventory = For the coarse-grained model, we train the model by splicing personality trait reports into queries.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 3. HPuLU6q7xq / paper-named_gpt-4_baseline

```text
issue_type = missing_baseline
origin = critique_payload
claim_ids = claim-3
missing = same-setting comparison against paper-named GPT-4 baseline
claim_anchor = Orca achieves state-of-the-art performance on the OrcaBench evaluation benchmark compared to existing methods.
inventory_locator = Table/Figure caption: Basic statistics for OrcaData.
inventory = the agent's psychological activities and personality traits.} \end{figure} \begin{table}[ht] \centering \begin{minipage}{0.45\textwidth} \centering \caption{Basic statistics for OrcaData.} \resizebox{\linewidth}{!}{ \sma
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 4. NnExMNiTHw / acceptance_prediction_head

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1, claim-2
missing = acceptance prediction head
claim_anchor = SpecDec++ reduces inference latency compared to fixed-K baselines by adaptively selecting the candidate length.
inventory_locator = Section: SpecDec++: Theory and Algorithm
inventory = Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1\textwidth]{figs/main.pdf} \caption{\ours uses a trained \textbf{acceptance prediction head} to predi
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 5. QAgwFiIY4p / coordinates_without_information_loss

```text
issue_type = missing_ablation
origin = critique_payload
claim_ids = claim-1
missing = y coordinates without information loss
claim_anchor = The paper introduces a novel graph-to-set conversion method that bijectively transforms interconnected nodes into a set of independent points.
inventory_locator = Section: Conclusion
inventory = We introduce a novel approach employing symmetric rank decomposition to transform interconnected nodes in graph into independent points with coordinates.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 6. WpXq5n8yLb / recurrent_draft_model

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-1, claim-2, claim-3, claim-4
missing = component-isolation ablation for recurrent neural network
claim_anchor = ReDrafter is an advanced speculative decoding approach that achieves state-of-the-art speedup for LLM inference.
inventory_locator = paper component inventory #1
inventory = Additionally, we incorporate the embeddings of historical tokens as recurrent inputs to the draft head.
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 7. YXn76HMetm / paper-named_pixelpick_baseline

```text
issue_type = missing_baseline
origin = critique_payload
claim_ids = claim-3
missing = same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL baseline
claim_anchor = HALO achieves superior empirical performance compared to established baselines like EqualAL across multiple domain shift scenarios.
inventory_locator = Table: results table
inventory = approach on a novel dataset, as shown in Table \ref{tab:results_table}c. \subsection{Ablation study} \label{sec:ablation} \input{tables/ablation_tables} We begin by conducting an oracular study using ground-truth labels,
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 8. fGXyvmWpw6 / efficiency_resource_measurement

```text
issue_type = efficiency_cost_gap
origin = critique_payload
claim_ids = claim-1, claim-3, claim-4
missing = runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim
claim_anchor = FVL achieves computational efficiency gains, such as reduced runtime or lower communication overhead, compared to baseline FL methods.
inventory_locator = Section: Method
inventory = updating. On the contrary, we update our global virtual data during FL training. \begin{table}[t] \centering \caption{Averaged test accuracy for \texttt{CIFAR10C} with ConvNet.} \resizebox{0.95\textwidth}{!}{ \begin{tabu
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO

### 9. ye3NrNrYOY / fixed_module

```text
issue_type = missing_ablation
origin = deterministic_seed
claim_ids = claim-3
missing = fixed module; ablation isolating encoder/backbone or its named component; ablation isolating aspects of the causal mechanism module
claim_anchor = The method's design choice of holding certain aspects of the causal mechanism fixed during adaptation is validated.
inventory_locator = Limitation / Gap / Negative evidence excerpt #1
inventory = We run an ablation study to select the hyperparameters of our model. We compare ${\mathrm{TCMT}}_{C}$ with the different numbers of latent causal variables $^{\prime}N\in\{4,8,12,16\})$ using the ViT-B/16 backbone for
```

Manual label: **TODO**

Decision: TODO

Rationale:

- TODO
