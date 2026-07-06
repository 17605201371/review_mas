# P32 Narrative Evidence Report

- status: **PASS**
- source stability: `P32_STABILITY_R1_R3_PRECISION_20260706.json`
- included runs: `2`
- recurring Critique-origin A/B clusters: `5`
- Critique-origin cluster Jaccard mean: `1.000`
- manual D clusters total: `0`
- harmful recovery total: `0`

## Run Evidence

| run | rows | machine | manual | A/B | D | Critique A/B | contested commits | harmful recovery |
|---|---:|---|---|---:|---:|---:|---:|---:|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | 20 | PASS | PASS | 7 | 0 | 5 | 20 | 0 |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | 20 | PASS | PASS | 7 | 0 | 5 | 16 | 0 |

## Recurring Critique-Origin Clusters

### `fgxyvmwpw6|efficiency_cost_gap|efficiency_resource_measurement`

- issue: `efficiency_cost_gap` / `efficiency_resource_measurement`
- recurrence: `2` runs
- manual labels: `A`
- runs with contested recovery support: `2` / `2`

| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |
|---|---|---|---|---|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | A | The proposed method is computationally efficient, reducing communication rounds and training time compared to other met... | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | Despite Federated Learning (FL)'s trend for learning machine learning models in a distributed manner, it is susceptible... | 2 | Tie the issue to empirical support for efficiency/resource-cost claims, not to the accuracy contribution. |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | A | FVL achieves computational efficiency gains, such as reduced runtime or lower communication overhead, compared to basel... | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | updating. On the contrary, we update our global virtual data during FL training. \begin{table}[t] \centering \caption{A... | 2 |  |

### `ge6iywjtsv|missing_ablation|graph_control_module`

- issue: `missing_ablation` / `graph_control_module`
- recurrence: `2` runs
- manual labels: `A, B`
- runs with contested recovery support: `2` / `2`

| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |
|---|---|---|---|---|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | B | The paper introduces a novel constrained diffusion model (Diff-Shape) and a Graph ControllNet (GrCN) for shape-based de... | graph control module; component-isolation ablation for with a graph control module | In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and... | 2 | Acknowledge the existing MIDI/SQUID/ShapeMol comparisons; limit the issue to component isolation of GrCN/graph control. |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | A | Diff-Shape introduces a novel constrained diffusion model for shape-based de novo drug design. | graph control module; component-isolation ablation for with a graph control module | In Diff-Shape method, a novel equivariant neural network architecture,named Graph ControllNet (GrCN), was proposed and... | 2 |  |

### `hpulu6q7xq|missing_baseline|paper-named_gpt-4_baseline`

- issue: `missing_baseline` / `paper-named_gpt-4_baseline`
- recurrence: `2` runs
- manual labels: `B`
- runs with contested recovery support: `2` / `2`

| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |
|---|---|---|---|---|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | B | The Orca method empirically outperforms baseline methods on role-playing tasks. | same-setting comparison against paper-named GPT-4 baseline | \caption{An example interaction between an personalized agent object of Orca and human on social platform. | 1 | Frame as absence of a strong closed-model reference point, not proof that GPT-4 was required or feasible. |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | B | Orca achieves state-of-the-art performance on the OrcaBench evaluation benchmark compared to existing methods. | same-setting comparison against paper-named GPT-4 baseline | the agent's psychological activities and personality traits.} \end{figure} \begin{table}[ht] \centering \begin{minipage... | 1 | Use careful wording; treat as defensible concern rather than confirmed defect. |

### `nnexmnithw|missing_ablation|acceptance_prediction_head`

- issue: `missing_ablation` / `acceptance_prediction_head`
- recurrence: `2` runs
- manual labels: `A, B`
- runs with contested recovery support: `2` / `2`

| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |
|---|---|---|---|---|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | B | SpecDec++ formulates the candidate length selection as an MDP and implements an adaptive policy to choose K. | acceptance prediction head; component-isolation ablation for of the acceptance prediction head | Theory and Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraph... | 3 | Phrase as missing isolation of the learned head/calibration choices, not as absence of all baseline comparisons. |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | A | SpecDec++ reduces inference latency compared to fixed-K baselines by adaptively selecting the candidate length. | acceptance prediction head | Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering \includegraphics[width=1... | 2 |  |

### `yxn76hmetm|missing_baseline|paper-named_pixelpick_baseline`

- issue: `missing_baseline` / `paper-named_pixelpick_baseline`
- recurrence: `2` runs
- manual labels: `B`
- runs with contested recovery support: `2` / `2`

| run | label | claim anchor | missing/mismatch | inventory/quote | recovery | caution |
|---|---|---|---|---|---:|---|
| P32_CLEAN_R1_PRECISION_RECOMPUTE_20260705_232527 | B | The HALO method empirically outperforms baseline methods (including EqualAL) for active learning semantic segmentation... | same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL bas... | HALO sets a new state-of-the-art in active learning for semantic segmentation under domain shift and it is the first ac... | 1 | Frame as missing named AL baseline comparisons under comparable settings, not as absence of all SOTA/ADA baselines. |
| P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000 | B | HALO achieves superior empirical performance compared to established baselines like EqualAL across multiple domain shif... | same-setting comparison against paper-named PixelPick baseline; same-setting comparison against paper-named EqualAL bas... | approach on a novel dataset, as shown in Table \ref{tab:results_table}c. \subsection{Ablation study} \label{sec:ablatio... | 1 | Use careful wording; treat as defensible concern rather than confirmed defect. |

## Narrative Constraints

- This is clean hardneg20 repeat evidence, not a full39/domain-general benchmark claim.
- The recurrent items are obligation-grounded verified review issues; they are not all direct quote-grounded negative evidence.
- The report makes no accept/reject accuracy claim and does not touch PPO or rollout internals.
- The report summarizes existing strict verifier, manual-audit, and recovery artifacts; it does not relax any gate.
