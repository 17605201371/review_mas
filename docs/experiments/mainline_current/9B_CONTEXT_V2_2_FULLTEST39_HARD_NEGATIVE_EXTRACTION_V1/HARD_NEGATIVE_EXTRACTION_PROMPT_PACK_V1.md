# Hard-Negative Extraction Prompt Pack v1

## ye3NrNrYOY (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: ye3NrNrYOY
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=2 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] al., 2023; Zhang et al., 2023). However, given the immense variety of possible actions in the real world, there is a natural challenge of learning action representations with little training data. One promising approach for overcoming this lack of labeled data is few-shot learning (Cao et al., 2020; Perrett et al., 2021; Thatipelli et al., 2022). Few-shot learning involves training a model on a large (base) dataset, and then using a small number of samples from another (novel) dataset to update the model (e.g., tune parameters). We apply few-shot learning to action recognition, where the action labels in the

[negative] ViT (Ben Avraham et al., 2022) and ActionCLIP (Wang et al., 2021). Few-shot action recognition can be made more efficient by fixing parts of the learned model that do not get updated during the adaptation phase, as long as this can be done without sacrificing model performance. For example, VideoPrompt (Ju et al., 2022) tunes a feature extractor only partially and VL Prompting (Rasheed et al., 2023) only tunes an ancillary module on the novel data. Several metric-based approaches have been proposed in which a metric space is learned from base data and assumed to transfer to novel data without adjustment (Wang et

[results] etwork are updated. Inference. To perform inference we sample $\hat{\bf z}$ according to Eq. 6 using our encoder, and we either choose the maximum value (highest probability) from the prediction $\hat{\mathbf{y}}$ or choose the label whose text embedding maximizes cosine similarity. \section{3 EXPERIMENTS } \section{3.1 EXPERIMENTAL SETUP } We carry out two types of few-shot learning experiments; all-way- $\cdot\mathbf{k}$ -shot and 5-way-k-shot. In allway- $\cdot\mathbf{k}$ -shot we try to classify all action classes in the class for the novel dataset $\left({\mathcal{C}}_{n o v e l}\right)$ , while in

[empirical] ith little training data. One promising approach for overcoming this lack of labeled data is few-shot learning (Cao et al., 2020; Perrett et al., 2021; Thatipelli et al., 2022). Few-shot learning involves training a model on a large (base) dataset, and then using a small number of samples from another (novel) dataset to update the model (e.g., tune parameters). We apply few-shot learning to action recognition, where the action labels in the novel data differ from the base data, and these datasets can be drawn from significantly different distributions. One popular approach to few-shot action recognition is to

```

## uOrfve3prk (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: uOrfve3prk
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=3 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] success rate, which measures how well intervening on an interpretable feature causally results in the desired behavior in the model outputs, and (2) coherence-intervention tradeoff, which measures how well the causal interventions succeed without damaging the coherence of the model's outputs. We evaluate Logit Lens, Tuned Lens, sparse autoencoders, and linear probes, for these metrics on GPT2-small, Gemma2-2b, and Llama2-7b, comparing them to simpler but uninterpretable baselines of steering vectors and prompting. Our results show that while existing methods allow for intervention, they are inconsistent across

[negative] g vectors, $\hat{x}' = x + \alpha * v$, where $v$ is the steering vector or the weights of the linear probe. Note that $\alpha$ is a hyperparameter that must be tuned for each method, model, and sometimes even intervention feature and thus cannot be used to compare the effects of interventions across methods. In order to do so, we can instead measure the normalized difference between the latent vectors $x$ and $\hat{x}'$, to better understand the relationship between the degree of intervention performed and our various evaluation metrics. We also note that $\hat{x}$ and $\hat{x}'$ are not necessarily

[results] t the corresponding representations \textit{in place}, as is common practice with prior steering methods. Formally, the representation $x_t$ at token position $t$ and layer $l$ is edited to be $\hat{x_t}'$, ensuring a causal effect on all ensuing tokens $x_{t+1}, x_{t+2}, ..., x_T$. \subsection{Comparative Evaluation Across Methods and Models} \label{sec:method_eval} Given the overall lack of standardized evaluation of mechanistic interpretability methods, we intend for this work to serve as a starting point for systematic evaluation by evaluating methods in simple, easy-to-measure contexts. In particular, we

[empirical] maps intermediate latent representations to human-interpretable feature spaces, enabling interventions on these interpretable features, which can then be mapped back to latent representations to control model outputs. We introduce two new evaluation metrics: intervention success rate and the coherence-intervention tradeoff, designed to measure the accuracy of explanations and their utility in controlling model behavior. Our findings reveal that (1) although current methods allow for intervention, they are inconsistent across various models and features, (2) lens-based methods outperform others in achieving

```

## 9zEBK3E9bX (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: 9zEBK3E9bX
Current final-view: borderline_positive
Current support: real=3 nonabstract=3 empirical=3 groups=3
Current unresolved/flaw burden: targetless_unresolved=8 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] ch can help guarantee safety in control task. NuScenes Segmentation. As shown in Tab. 4, considerable gains are achieved by SPOT, 4.03 and $2.38\;\mathrm{mIOUs}$ on $5\%$ and $10\%$ NuScenes data respectively. SPOT also achieves the best performance among all initialization methods. \section{4.3 DISCUSSIONS AND ANALYSES } Pre-training Tasks. We argue that occupancy prediction is a scalable and general task for 3D representation learning. Here we conduct experiments to compare different kinds of existing task for pre-training, including detection and segmentation tasks. Pre-training is conducted on the full Waymo

[negative] o improve the performance in label-efficiency setting. Previous methods can be divided into two streams: (1) Embraced by AD-PT (Yuan et al., 2023), semi-supervised pre-training achieves a strong performance gain when using fewer labels but limited to specific task like 3D object detection (task-level gap). (2) Other works including GCC-3D (Liang et al., 2021), STRL (Huang et al., 2021), BEV-MAE (Lin & Wang, 2022), CO3 (Chen et al., 2022) and MV-JAR (Xu et al., 2023) utilize unlabeled data for pre-training. This branch of work fails to generalize across datasets with different LiDAR sensors and annotation

[negative] eling for 3D point clouds is time-and-energy-consuming. To reduce the labeling burden, previous works explore semi-supervised learning (Unal et al., 2022; Kong et al., 2023; Li et al., 2023a) and achieve excellent performance, but they are limited to specific task. In this work, we explore general 3D representation learning via large-scale pre-training. ![](images/4a7b865071076cf50b37e5d58458ed052c95675c6a60f1d7a02a54110cbc01c3.jpg) Figure 2: The overview of the proposed SPOT. Firstly, the input LiDAR point cloud is augmented by beam re-sampling to simulate various LiDAR sensors, which helps learn general

[results] ssign weight $w_{\mathrm{fg}}\,=\,2.0$ to common foreground categories including car, pedestrian, cyclist, bicycle, and motorcycle. Meanwhile, other background categories like vegetation and road are assigned $w_{\mathrm{bg}}=1.0$ and $w_{\mathrm{empty}}=0.01$ for unoccupied voxels. \section{4 EXPERIMENTS } The goal of pre-training is to learn general representations for various downstream tasks, datasets, and architectures. In this section, we design extensive experiments to answer the question whether SPOT learns such representations in a label-efficiency way. We first introduce experiment setup in Sec. 4.1,

```

## WpXq5n8yLb (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: WpXq5n8yLb
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=2 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] maintaining a separate draft model. However, Medusa necessitates multiple draft heads with distinct parameters to indicate predictive positions. Its independent prediction mechanism does not leverage the sequential structure, resulting in limited predictive accuracy and an exponentially large set of feasible candidate token sequences. In this paper, we introduce the Recurrent Drafter (ReDrafter), for fast LLM inference. Figure~\ref{fig:redrafter_demo} illustrates its generative process. ReDrafter's performance gains are driven by three key aspects: (1) Using a recurrent neural network

[negative] requests while maintaining low latency. In this scenario, ReDrafter achieves up to 2.5x speedup on the MT-bench benchmark. The second use case focuses on an on-device approach using MLX on Metal GPUs within Apple Silicon chips. Despite the limited compute resources in this setup, we observed a memory bottleneck. ReDrafter effectively mitigates this bottleneck, resulting in up to 2.3x speedup, demonstrating its capability to optimize performance in resource-constrained environments. \begin{figure}[t] \centering \includegraphics[width=\textwidth]{ICLR2025_submission/figures/redrafter_demo_v3.pdf}

[results] ure the decoding results remain consistent. Additionally, we apply distillation locally by having the LLM predict the next $T$ tokens using the ground truth tokens as context. \cmnt{This approach is taken because LLM occasionally produces unreasonable predictions in long sequences.} \section{Experiment} We conduct experiments in experimental and production-ready environments, using Vicuna 7B, 13B, 33B models as base LLMs. First, using PyTorch, we compare ReDrafter with state-of-the-art speculative decoding methods on an Nvidia H100 GPU in Section~\ref{subsec:exp_pytorch_benchmark}. Next, we validate ReDrafter's

[empirical] lly, we apply distillation locally by having the LLM predict the next $T$ tokens using the ground truth tokens as context. \cmnt{This approach is taken because LLM occasionally produces unreasonable predictions in long sequences.} \section{Experiment} We conduct experiments in experimental and production-ready environments, using Vicuna 7B, 13B, 33B models as base LLMs. First, using PyTorch, we compare ReDrafter with state-of-the-art speculative decoding methods on an Nvidia H100 GPU in Section~\ref{subsec:exp_pytorch_benchmark}. Next, we validate ReDrafter's performance gain in a production-ready environment on

```

## NnExMNiTHw (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: NnExMNiTHw
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=4 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] 4.13$ tokens/second (2.92x speedup) according to Equation~\eqref{eq:costfn2} with the empirical value of $(t_{\text{target}},t_{\text{draft}})$ reported in Section~\ref{sec:time}. In comparison, the average throughput for the target model without speculative decoding is 9.26 tokens/second, while speculative decoding with the best fixed $K$ gives 17.58 tokens/second (1.90x speedup) (Section~\ref{sec:exp}). We see that there is a huge potential in adaptively tuning the candidate lengths. \section{SpecDec++: Theory and Algorithm} \label{sec:method} \newcommand{\Hid}{{\boldsymbol{e}}} \begin{figure}[t] \centering

[results] } Y_i}} \Big(- w_{\text{acc}}\cdot \PP_i \log \hat{\PP}_i - w_{\text{rej}}\cdot (1-\PP_i) \log (1-\hat{\PP}_i) \Big), \] where $w_{\text{acc}}$ and $w_{\text{rej}}$ are the weights and $\hat{\PP}_i = \mathrm{sigmoid}(f_\theta(\Hid_i(x_{\text{prompt}}, Z_1,\dots,Z_{i-1},Y_{i})))$. \section{Experiments} \label{sec:exp} \subsection{Experimental Setups} \label{sec:exp:setup} \textbf{Datasets and Model Pairs.} We adopt three datasets in our experiments: Alpaca~\citep{alpaca}, HumanEval~\citep{chen2021evaluating}, GSM8K~\citep{cobbe2021training}. We only use prompts of the datasets and do not use responses. In the

[empirical] ulation when the predicted probability that \textit{at least one token gets rejected} exceeds a threshold. We implement \ours and apply it to the llama-2-chat 7B \& 70B model pair. Our adaptive method achieves a 2.04x speedup on the Alpaca dataset (an additional 7.2\% improvement over the baseline speculative decoding). On the GSM8K and HumanEval datasets, our method achieves a 2.26x speedup (9.4\% improvement) and 2.23x speedup (11.1\% improvement), respectively. \end{abstract} \section{Introduction} \label{sec:intro} Current state-of-the-art Large Language Models (LLMs) have demonstrated extraordinary

[empirical] ns the acceptance probability of the current candidate token is large compared to other cases. \begin{figure}[t] \centering \includegraphics[width=0.95\textwidth]{figs/teaser_result.pdf} \caption{The performance of \ours. Compared with the baseline speculative decoding (SpecDec) with fixed candidate lengths, by adaptively determining the candidate lengths via a trained acceptance prediction head, \ours achieves a relative \textbf{7.2\%}, \textbf{11.1\%}, and \textbf{9.4\%} improvement over the baseline methods on the Alpaca, HumanEval, and GSM8K dataset, respectively. The experiments are conducted with

```

## cklg91aPGk (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: cklg91aPGk
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=3 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] werful alternative: uniform propagation, abbreviated as PROP, which involves no trainable layers. Remarkably, PROP demonstrates competitive performance on various node classification benchmarks, often matching or surpassing more sophisticated GCLs. This raises an important question: \section{5 DISSECTING THE LIMITATIONS OF GNNS IN GCL } The preceding experiments reveal that existing GCL methods perform worse than the simple PROP. In this section, we seek to understand the rationale behind this. For this aim, we analyze the decoupling of the propagation and transformation phases, a widely adopted perspective in

[negative] literature and proven effective in various works (Bauw et al., 2021; Li et al., 2006; Freund et al., 2007), GCL should aim to learn weights tailored on data, rather than relying on a random matrix. Therefore, the results indicate that GCL fails to learn informative transformation weights as expected. We hypothesize the failure stems from the unsupervised nature of the task, which leads to inefficient optimization in the absence of sufficient guidance. Empirically, we compare the difference between the transformation weights learned by supervised learning (SL) and GCL. Figure 1(a) and Figure 1(b) illustrate the

[negative] meters in both, GCLs utilizing polynomial GNNs, as shown in Section 4.2, tend to underperform. This issue has been recognized in prior work, often attributed to the mismatch between the strong fitting capacity of polynomial filters and the lack of supervision signals in self-supervised learning (Chen et al., 2022; 2024). However, through the following experiments, we demonstrate that GCLs are capable of learning effective filters. From the decoupling perspective, there are three conjectures as to why polynomial GNNs perform poorly in GCL: 1) GCL learns suboptimal transformation weights, 2) GCL learns ineffective

[results] rmation weights W with well-trained parameters from a supervised setting. Specifically, we first train polynomial GNNs via supervised learning and save the optimized parameters as $\mathbf{W}_{\mathrm{SL}}$ and $\theta_{\mathrm{SL}}$ . We then proceed with the following experiments: Experiment 1 (Fix-propagation). Corresponding to the first conjecture, we initialize and freeze $\pmb{\theta}$ with the well-trained $\theta_{\mathrm{SL}}$ , and only learn W through GCL. Representations are generated by the fixed propagation coefficients and learned transformation weights. Experiment 2 (Fix-transformation).

```

## QAgwFiIY4p (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: QAgwFiIY4p
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=5 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] ur approach demonstrates remarkable theoretical expressivity and excels in real-world performance, addressing both short-range and long-range tasks effectively. It extends the design space of GNN and provides a principled way to inject graph structural information into Transformers. \section{Limitations} PST's scalability is still constrained by the Transformer architecture. To overcome this, acceleration techniques such as sparse attention and linear attention could be explored, which will be our future work. --- END OF PAPER --- Task: Now provide the review for the paper above. Follow the format exactly.

[negative] oordinate}. This representation enables us to express the presence of edges as inner products of coordinate vectors ($Q_i$ and $Q_j$). Consequently, interlinked nodes can be transformed into independent points and supplementary coordinates without information loss. Theoretically, two graphs are isomorphic iff the two converted point sets are equal up to an \textit{orthogonal transformation} (because for any $QQ^T=A+D$, $QR$ is also a solution where $R$ is any orthogonal matrix). This equivalence empowers us to encode the set with coordinates in an orthogonal-transformation-equivariant manner, akin to

[negative] down the interconnections between nodes is to decompose the adjacency matrix. While previous methods often used eigendecomposition outputs as supplementary node features, these features are not unique. Consequently, models relying on them fail to provide consistent predictions for isomorphic graphs, ultimately leading to poor generalization. To address this, we show that Symmetric Rank Decomposition (SRD) can convert graph-level tasks into set-level tasks with perfect alignment. \begin{theorem}\label{thm::g2s} Given two graphs $\mathcal{G}=(V, A,X)$ and $\mathcal{G'}=(V',A',X')$ with respective degree matrices

[results] roducts of coordinates. Additionally, these prior works center on 3D point spaces, whereas our coordinates exist in high-dimensional space, rendering existing models and theoretical expressivity results based on high-order irreducible representations incompatible with our framework. \section{Experiments} In our experiments, we evaluate our model across three dimensions: substructure counting for short-range expressivity, real-world graph property prediction for practical performance, and Long-Range Graph Benchmarks~\citep{LRGB} to assess long-range interactions. Our primary model, Point Set Transformer (PST)

```

## KI9NqjLVDT (accept)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: KI9NqjLVDT
Current final-view: borderline_positive
Current support: real=3 nonabstract=3 empirical=3 groups=3
Current unresolved/flaw burden: targetless_unresolved=6 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] e, with results summarized in Table~\ref{tab:baseimputer}. It is observed that compared with the default setting (with mean substitution as the base imputer), using \model as the base imputer improves the imputation performance, suggesting another effective way of operating \model. \section{Discussion} \label{sec:discussion} \textbf{Theoretical justification.} The empirical evaluation above shows \model's superior performance in imputing missing values of tabular data. Next, we provide theoretical justification for its effectiveness. By extending the siamese form of MAE~\cite{mim}, we show that \model encourages

[negative] tasets, we show that \model performs on par with or outperforms state-of-the-art methods in terms of both imputation fidelity and utility under various missingness settings, while its performance advantage often increases with the ratio of missing data. We further explore theoretical justification for its effectiveness, showing that \model tends to learn missingness-invariant representations of tabular data. Our findings indicate that masked modeling represents a promising direction for further research on tabular data imputation. The code is publicly available \end{abstract} \section{Introduction}

[results] \; \State $\bar{\rvx}_{\overline{\rvm}} \gets d_\vartheta(\rvz)$; \Comment{// predicting missing values} \State $\hat{\rvx} \gets \tilde{\rvx}_\rvm \cup \bar{\rvx}_{\overline{\rvm}}$; \EndFor \State \textbf{return} $\hat{\gD} = \{\hat{\rvx} \} $. \end{algorithmic} \end{algorithm} \section{Evaluation} \label{sec:eval} We evaluate the empirical performance of \model in various scenarios using benchmark datasets. Our experiments are designed to answer the following key questions: \mct{i} {\em Does \model work?} -- We compare \model with a variety of state-of-the-art imputers in terms of imputation quality. \mct{ii}

[empirical] s and impute missing values by querying the trained models. Empirically, GAN-based methods often require a large amount of training data and suffer the difficulties of adversarial training~\cite{gan}, while VAE-based methods often face the limitations of training through variational bounds~\cite{vae-understanding}. \rev{Further, some of these methods either require complete data during training or operate on the assumptions of specific missingness patterns.} In this paper, we present \model, a novel method that extends the masked autoencoding (MAE) framework~\cite{bert,mae} to imputing missing values of tabular

```

## TPAj63ax4Y (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: TPAj63ax4Y
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=6 ungrounded_candidate_flaws=1 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] owing the model to choose between the training masks in greedy matching, the model is able to recover from the incorrect zero-shot choice in these cases -- this effect is compounded over the training epochs as better matching initially leads to quicker correction of future mistakes. \section{Discussion and Limitations} We propose a three-stage pipeline for weakly-supervised RIS that obtains all the instance masks for the referred object (\textit{segment}), gets a good first guess on the right one using a zero-shot instance choice method (\textit{select}), and then bootstrap and corrects it through the

[negative] method is summarized in Figure~\ref{fig:overview-instance}. Our main contributions are: (1) we introduce \textit{segment}, \textit{select}, \textit{correct} (\ours) as a three-stage framework to perform referring image segmentation \textbf{without supervised referring masks} by training a model on pseudo-masks obtained using a zero-shot pipeline; (2) we establish new state-of-the-art performance in both zero-shot and weakly-supervised RIS, outperforming the zero-shot method by \cite{yu2023zero} by as much as $19\%$, and the weakly-supervised methods by \cite{liu2023referring, kim2023shatter} by significant

[negative] aset of the form $\mathcal{D} = \{\img_i, \{\sent_{i, j, k}\}_{k=1}^{n^\mathbf{O}_{i,j}}\}_{i=1}^{n^\img}$, where each object $\mathbf{O}_{i,j}$ of the $n_{ij}^O$ existing objects is implicitly described by the set of referring expressions without \textit{a priori} knowledge of its mask. This is the setup from previous works \cite{strudel2022weakly, liu2023referring, kim2023shatter}. \textbf{CLIP.} We use the text and image encoders of CLIP \cite{radford2021learning}, which we refer to as $\psi_{\text{CLIP}}: \mathcal{T} \to \mathbb{R}^{e}$ and $\phi_{\text{CLIP}}: \mathbb{R}^{\mathcal{I}} \to \mathbb{R}^{e}$,

[results] st{\textbf{49.78}}\\ \midrule FS & \supcolor{LAVT} \cite{yang2022lavt} & \supcolor{74.46} & \supcolor{76.89} & \supcolor{70.94} & \supcolor{65.81} & \supcolor{70.97} & \supcolor{59.23} & \supcolor{63.34} & \supcolor{63.62} & \supcolor{63.66}\\ \bottomrule \end{tabular} } \end{table} \section{Experiments} \label{sec:experiments} The aim of this section is to showcase the effectiveness of our method in closing the gap of zero-shot and weakly-supervised methods with the fully-supervised state-of-the-art using only images and referring sentences. To achieve this, we report results on: \begin{itemize} \item

```

## xUe1YqEgd6 (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: xUe1YqEgd6
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=5 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] a volume of consecutive optical flows, and delivers consistent motion segmentation maps throughout the video sequence. It involves a transformer module allowing for long-term interactons. It is trained in a completely unsupervised manner, without any manual annotation or ground truth data of any kind. The loss function is inferred by leveraging the Evidence Lower Bound (ELBO) framework, and comprises a flow reconstruction term with original spatio-temporal parametric motion models and an additional term enforcing temporal consistency on the segmentation masks. We model with B-splines the long-term temporal

[negative] hod (16) involves learnable motion models, and is structured in two stages, a motion-supervised object discovery stage, and then, a refinement stage with residual motion prediction and high-level appearance supervision. However, the method cannot distinguish objects undergoing different motions. In (6), the prediction of probable motion patterns is used at the training stage as a cue to learn objectness from videos. Divided attention is promoted in (14). The resulting DivA method is based on the same principle as in (36) that motion segments are mutually uninformative. However, it is not limited to binary

[results] e FlyingThings3D (FT3D) dataset (20), whatever the dataset considered at test time. This ensures that our LT-MS network generalizes well to unseen datasets. Regarding hyperparameter setting, we select the stopping epoch from the loss function evaluated on the DAVIS2016 training set. \section{5 EXPERIMENTAL RESULTS } We have carried out comparative experiments on four datasets: DAVIS $2016^{1}$ (26), SegTrackV22 (15), FBMS59 (24), and DAVIS2017-motion (33). \section{5.1 ABLATION STUDY } We have conducted an ablation study to assess three main components of our method LT-MS with four masks $(K\,=\,4)$ ), in

[empirical] ion. Section 3 presents our unsupervised network for multiple motion segmentation in one go, embedding long-term temporal consistency. In Section 4, we provide implementation details. Section 5 reports results on four VOS benchmarks with a comparison to state-of-the-art unsupervised motion segmentation methods. Finally, Section 6 contains concluding remarks. \section{2 RELATED WORK } Motion segmentation aims to break down each frame of a video sequence into components (or segments) of coherent motion. Usually, each motion segment is identified by a motion model, which can be hand-crafted such as affine or

```

## jVEoydFOl9 (accept)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: jVEoydFOl9
Current final-view: borderline_positive
Current support: real=4 nonabstract=4 empirical=2 groups=3
Current unresolved/flaw burden: targetless_unresolved=7 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] tates with the unconditional R-GATv2 encoder. We therefore posit that conditional representations (both on relation and entity levels) are crucial for transferable representations for link prediction tasks that often require pairwise representations to break neighborhood symmetries. \section{Discussion and Future Work} \label{sec:conclusion} \textbf{Limitations and Future Work.} Albeit \method demonstrates promising capabilities as a foundation model for KG reasoning in the zero-shot and fine-tuning regimes, there are several limitations and open questions. First, pre-training on more graphs does not often

[negative] ey problem is that different KGs typically have different entity and relation vocabularies. Classic \emph{transductive} KG embedding models~\citep{ali2021light} learn entity and relation embeddings tailored for each specific vocabulary and cannot generalize even to new nodes within the same graph. More recent efforts towards generalization across the vocabularies are known as \emph{inductive} learning methods~\citep{chen2023generalizing}. Most of the inductive methods~\citep{grail,nbfnet,nodepiece,redgnn} generalize to new entities at inference time but require a fixed relation vocabulary to learn entity

[negative] any relations at inference. ISDEA~\citep{isdea} is the first approach to design doubly equivariant GNNs and MTDEA~\citep{mtdea} further extends the theory to partial equivariance. However, ISDEA and MTDEA are computationally expensive and cannot scale to graphs considered in this work. Similarly to RMPI, InGram, ISDEA, and MTDEA, \method %does not impose any assumptions on relations, transfers to \emph{any} unseen KG in the zero-shot fashion, but exhibits better generalization capabilities, scales to graphs of millions of edges, and introduces only a marginal inference overhead (one-step pre-computation) to any

[results] KG completion. Since the method does not learn any graph-specific entity or relation embeddings nor requires any input entity or relation features, %any model pre-trained with \method enables \emph{zero-shot} generalization to any other KG of any size and any relational vocabulary. Experimentally, we show that \method paired with the NBFNet~\citep{nbfnet} link predictor pre-trained on three KGs (FB15k-237, WN18RR, and CoDEx-M derived from Freebase, WordNet, and Wikidata, respectively) generalizes to 50+ different KGs with sizes of 1,000--120,000 nodes and 5K--1M edges. \method demonstrates promising transfer

```

## YXn76HMetm (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: YXn76HMetm
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=2 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] rom inaccuracies, as identified by prediction uncertainty, but also from the information the model has been exposed to thus far, including the amount of data considered. In the domain adaptation task, the domain gap arises from the model's lack of understanding of the new domain data, akin to the definition of epistemic uncertainty. Building upon this intuition, we propose HALO (Hyperbolic Active Learning Optimization), a novel approach for active domain adaptation, where we introduce the use of epistemic uncertainty into the data acquisition strategy. Our in-depth analysis shows that the hyperbolic radius

[negative] ~\citep{atigh2022hyperbolic} trains with class hierarchies, which they manually define. As a result, their hyperbolic radius represents the parent-to-child hierarchical relations in the Poincaré ball. We adopt ~\citet{atigh2022hyperbolic} without enforcing hierarchical labels and we find that hierarchical relationships do not emerge naturally in our case. For instance, in HALO, classes such as \emph{road} and \emph{building} are closer to the center of the ball, while \emph{person} and \emph{rider} have larger radii. This class arrangement contradicts the interpretation of the hyperbolic radius as a proxy for

[results] \title{Hyperbolic Active Learning for Semantic Segmentation under Domain Shift} \begin{abstract} We introduce a hyperbolic neural network approach to pixel-level active learning for semantic segmentation. Analysis of the data statistics leads to a novel interpretation of the hyperbolic radius as an indicator of data scarcity. In HALO (Hyperbolic Active Learning Optimization), for the first time, we propose the use of epistemic uncertainty as a data acquisition strategy, following the intuition of selecting data points that are the least known. The hyperbolic radius, complemented by the widely-adopted prediction

[empirical] and \emph{building} are closer to the center of the ball, while \emph{person} and \emph{rider} have larger radii. This class arrangement contradicts the interpretation of the hyperbolic radius as a proxy for uncertainty, which emerged from metric learning hyperbolic studies~\citep{ermolov2022hyperbolic,franco23}. In our context, larger radii indicate larger data scarcity, therefore less certainty, which is in contrast with \citet{franco23}'s interpretation. Thus, our interpretation of the hyperbolic radius as a proxy for data scarcity does not align with neither of the existing interpretations in the case of

```

## KOUAayk5Kx (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: KOUAayk5Kx
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=9 ungrounded_candidate_flaws=1 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] l. (2018); Brock et al. (2017). The key of the one-shot NAS is weight sharing Guo et al. (2020a); Dong & Yang (2019a); Guo et al. (2020b); Chu et al. (2021), where the weights of all candidate architectures directly inherit from a supernet without training from scratch Hu et al. (2021); Chen et al. (2021); Yu et al. (2021). In this way, only the supernet needs to be trained during the architecture search, and the training time can be reduced from days to several hours, so that the search efficiency is greatly improved Yu et al. (2020); Dong & Yang (2019b). Although the weight sharing can significantly enhance

[negative] nced projection based on PCA is designed to find a set of base vectors to represent the gradient space of all previously trained architectures, which overcomes the projector attenuation issue and helps to determine the orthogonal direction without need to store the gradient vectors of all previously trained architectures. ![](images/4fb92a21b5f5f08d5f829e4c0ca4fd4e2f24e5ad1cf5fe66c448eefb94904fd9.jpg) Figure 2: Difference between SGD and OGL in the training of the overlapped structures of architecture $B$ after the training of architecture $A$ . The updating direction of the weights in SGD is towards the low

[results] ges/bc382d6a28ab2a065518828f909a690ddd708c08921253e03b7113411d21a3a0.jpg) Figure 3: The best cells discovered on CIFAR-10. (a) Normal cell searched by(b) Reduction cell searched(c) Normal cell searched by(d) Reduction cell searched RandomNAS-OGL by RandomNAS-OGL GDAS-OGL by GDAS-OGL \section{4 EXPERIMENT } \section{4.1 ONE-SHOT NAS WITH OGL } In this study, we apply OGL to two popular single-path one-shot NAS baselines, including the RandomNAS Li & Talwalkar (2020) and GDAS Dong & Yang (2019b), where RandomNAS and GDAS are random- and gradient-based sampling NAS methods, respectively. For convenience, our

[empirical] ent space to acquire the orthogonal direction. We have theoretically and experimentally proved the effectiveness of the proposed paradigm in overcoming the multi-model forgetting. Besides, we apply the proposed paradigm to two one-shot NAS baselines, and experimental results have demonstrated that our approach is able to mitigate the multi-model forgetting and enhance the predictive ability of the supernet in one-shot NAS with remarkable efficiency on popular test datasets. \end{abstract} \section{1 INTRODUCTION } Recent years, one-shot neural architecture search (one-shot NAS) has aroused massive interests and

```

## WLgbjzKJkk (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: WLgbjzKJkk
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=1 groups=2
Current unresolved/flaw burden: targetless_unresolved=3 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[limitations] th MOTRv2 while maintaining similar FLOPs (173G) and number of parameters(40M) with MOTR. The runtime speed of CO-MOT is much faster $_{(1.4\times)}$ than MOTRv2’s. Thus, our approach is effective and efficient, which is friendly for deployment as it does not need an extra detector. \section{4.6 LIMITATIONS } Despite the introduction of COLA and Shadow, which improve the tracking effect of MOTR, the inherent data-hungry nature of the Transformer model means that there is not a significant improvement in smaller datasets like MOT17. As shown in Figure 5a, a prominently visible target has not been detected, but

[negative] ifically, we add tracked objects to the matching targets for detection queries when performing the label assignment for training the intermediate decoders. For query initialization, we expand each query by a set of shadow counterparts with limited disturbance to itself. With extensive ablations, Co-MOT achieves superior performance without extra costs, \textit{e.g.}, 69.4\% HOTA on DanceTrack and 52.8\% TETA on BDD100K. Impressively, Co-MOT only requires 38\% FLOPs of MOTRv2 to attain a similar performance, resulting in the 1.4$\times$ faster inference speed. Codes are attached for re-implementation.

[negative] l. (2016)), motion prediction( Lefe\`vre et al. (2014); Welch et al. (1995)), and temporal association( Kuhn (1955)). The sparkling advantage of this paradigm is task decomposition, leading to an optimal solution for each task. However, it lacks global optimization for the whole pipeline. Recently, end-to-end Multi-Object Tracking (e2e-MOT) via Transformer such as MOTR( Zeng et al. (2022)) and TrackFormer( Meinhardt et al. (2022)) has emerged, which performs detection and tracking simultaneously in unified transformer decoders. Specifically, tracking queries realize identity tracking by recurrent attention over

[results] e representative is higher than a certain threshold $\tau$ , we select the box and score predictions of the shadow with the highest score as the tracking outputs and feed the entire set to the next frame for subsequent tracking. Sets that do not capture any object will be discarded. \section{4 EXPERIMENT } Table 2: Comparison to state-of-the-art methods on different dataset. Please pay more attention to the metrics with blue. (a) Comparison to existing methods on the DanceTrack test set. ”\*”, ”+” respectively represent the use of DAB-Deformable backbone and joint training with CrowdHuman. Best results of

```

## LieTse3fQB (reject)

```text
# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{
  "hard_negative_candidates": [
    {"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}

Paper id: LieTse3fQB
Current final-view: borderline_positive
Current support: real=2 nonabstract=2 empirical=2 groups=2
Current unresolved/flaw burden: targetless_unresolved=3 ungrounded_candidate_flaws=0 fallback_or_meta_flaws=1

# Hard-Negative Context
[negative] ussians overfitted to every training view, which degrades the rendering quality. Additionally, while 3D Gaussian Splatting excels in small-scale and object-centric scenes, its application to larger scenes is hindered by constraints such as limited video memory, excessive optimization duration, and variable appearance across views. To address these challenges, we introduce GaussianFocus, an innovative approach that incorporates a patch attention algorithm to refine rendering quality and implements a Gaussian constraints strategy to minimize redundancy. Moreover, we propose a subdivision reconstruction strategy

[negative] (SfM) (Snavely et al., 2006) to model scenes with inherent volumetric continuity, facilitating fast rasterization by projecting onto 2D planes. However, 3DGS often produces artifacts when camera viewpoints deviate from the training set and lack detail during zooming. To address these issues, newer models (Yu et al., 2024; Lu et al., 2024) employ a 3D smoothing filter to regularize the maximum frequency and utilize anchor points to initialize 3D Gaussians, thereby enhancing visual accuracy and applicability in diverse scenarios. Despite these advances, 3DGSbased models still tend to use oversized Gaussian spheres

[results] l., 2022). Each approach is rendered in four different resolutions (1/8, 1/4, 1/2, and the full resolution) after being trained at the lowest resolution (1/8). Our approach produces similar results at the 1/8 resolution and outperforms other models at 1/2, 1/4, and full resolutions. \section{4 EXPERIMENTS } \section{4.1 BASELINES } We selected Mip-Splatting (Yu et al., 2024) and 3D-GS (Kerbl et al., 2023) as our primary baseline due to their established state-of-the-art performance in novel view synthesis. In our evaluation, we included several other prominent techniques, such as Mip-NeRF360 (Barron et al.,

[empirical] e content as follows: Section 2 indicates the preliminary concepts. Section 3 outlines the methods we employed. In Section 4, we present our experimental framework compare its performance to other advanced 3DGS-based models and discuss the ablation studies. We conclude the paper in Section 5. \section{2 PRELIMINARIES } In the foundational aspects of the 3DGS framework (Kerbl et al., 2023), the scene is represented using anisotropic 3D Gaussians that integrate differential properties typical of a volume-based approach but are rendered more effectively through a grid-based rasterization technique. Beginning with a

```
