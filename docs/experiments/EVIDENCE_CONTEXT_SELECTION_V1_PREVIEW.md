# Evidence Context Selection v1 Preview

- Dataset: `outputs/subsets/state_hygiene_mixed_v2.parquet`
- Samples previewed: 5
- Runtime behavior changed: no model run; static context rendering only.

## cWEfRkYj46

- gold_decision: `accept`
- old_chars: 800
- new_chars: 2400
- cleaned_wrapper: `True`
- contains_method: `True`
- contains_results: `False`
- contains_conclusion: `True`
- contains_table_or_figure: `True`
- snippet_sources: `['abstract', 'method', 'table_or_figure', 'conclusion']`

### old_first_800_preview

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'. --- BEGIN PAPER --- \title{Towards Homogeneous Lexical Tone Decoding from Heterogeneous Intracranial Recordings} \begin{abstract} Recent advancements in brain-computer interfaces (BCIs) have enabled the decoding of lexical tones from intracranial recordings, offering the potential to restore the communication abilities of speech-impaired tonal language speakers. However, data heterogeneity induced by both physiological and instrumental factors poses a significant challenge for unified invasive brain tone decoding. Traditional subject-specific models, which operate under a het

### new_context_preview

[abstract] \title{Towards Homogeneous Lexical Tone Decoding from Heterogeneous Intracranial Recordings} \begin{abstract} Recent advancements in brain-computer interfaces (BCIs) have enabled the decoding of lexical tones from intracranial recordings, offering the potential to restore the communication abilities of speech-impaired tonal language speakers. However, data heterogeneity induced by both physiological and instrumental factors poses a significant challenge for unified invasive brain tone decoding. Traditional subject-specific models, which operate under a heterogeneous decoding paradigm, fail to capture generalized neural representations and cannot effectively leverage data across subjects. To [method] o address these limitations, we introduce \textbf{H}omogeneity-\textbf{H}eterogeneity \textbf{Di}sentangled \textbf{L}earning for neural \textbf{R}epresentations (H2DiLR), a novel framework that disentangles and learns both the homogeneity and heterogeneity from intracranial recordings across multiple subjects. To evaluate H2DiLR, we collected stereoelectroencephalography (sEEG) data from multiple participants reading Mandarin materials comprising 407 syllables, representing ...

## nrvoWOWcyg

- gold_decision: `accept`
- old_chars: 800
- new_chars: 2400
- cleaned_wrapper: `True`
- contains_method: `False`
- contains_results: `True`
- contains_conclusion: `True`
- contains_table_or_figure: `True`
- snippet_sources: `['abstract', 'results', 'table_or_figure', 'conclusion']`

### old_first_800_preview

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'. --- BEGIN PAPER --- \title{Chunk-Distilled Language Modeling} \begin{abstract} We introduce Chunk-Distilled Language Modeling (CD-LM), an approach to text generation that addresses two challenges in current large language models (LLMs): the inefficiency of token-level generation, and the difficulty of adapting to new data and knowledge. Our method combines deep network-based LLMs with a straightforward retrieval module, which allows the generation of multi-token text chunks at a single decoding step. Our retrieval framework enables flexible construction of model- or domain-spe

### new_context_preview

[abstract] \title{Chunk-Distilled Language Modeling} \begin{abstract} We introduce Chunk-Distilled Language Modeling (CD-LM), an approach to text generation that addresses two challenges in current large language models (LLMs): the inefficiency of token-level generation, and the difficulty of adapting to new data and knowledge. Our method combines deep network-based LLMs with a straightforward retrieval module, which allows the generation of multi-token text chunks at a single decoding step. Our retrieval framework enables flexible construction of model- or domain-specific datastores, either leveraging the internal knowledge of existing models, or incorporating expert insights from human-annotated corp [results] $ and $\beta$ values backward from $N$ to 2, we can get the marginal sequence probability under CD-LM as $$ p(x_{1:N}^{*})=p_{\theta}(x_{1}^{*})\left[\alpha_{2}q_{2}+\beta_{2}(1-q_{2})\right] $$ \section{6 EXPERIMENTS } We conduct experiments on multiple LMs and tasks. We formulate $g_{\phi}$ in Eq (3) as a simple piecewise linear function, where the maximum context matching similarity score only maps to a non-zero chunk acceptance probability $q_{n}$ if the score is larger...

## VEJzjAvaIy

- gold_decision: `accept`
- old_chars: 800
- new_chars: 2400
- cleaned_wrapper: `True`
- contains_method: `True`
- contains_results: `False`
- contains_conclusion: `True`
- contains_table_or_figure: `True`
- snippet_sources: `['abstract', 'method', 'table_or_figure', 'conclusion']`

### old_first_800_preview

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'. --- BEGIN PAPER --- \title{Divergence of Neural Tangent Kernel in Classification Problems} \begin{abstract} This paper primarily investigates the convergence of the Neural Tangent Kernel (NTK) in classification problems. This study firstly show the strictly positive definiteness of NTK of multi-layer fully connected neural networks and residual neural networks. Then, through a contradiction argument, it indicates that, during training with the cross-entropy loss function, the neural network parameters diverge due to the strictly positive definiteness of the NTK. Consequently,

### new_context_preview

[abstract] \title{Divergence of Neural Tangent Kernel in Classification Problems} \begin{abstract} This paper primarily investigates the convergence of the Neural Tangent Kernel (NTK) in classification problems. This study firstly show the strictly positive definiteness of NTK of multi-layer fully connected neural networks and residual neural networks. Then, through a contradiction argument, it indicates that, during training with the cross-entropy loss function, the neural network parameters diverge due to the strictly positive definiteness of the NTK. Consequently, the empirical NTK does not consistently converge but instead diverges as time approaches infinity. This finding implies that NTK theory [method] ision, natural language processing, and generative models. In the field of computer vision, Krizhevsky et al. (2012) proposed AlexNet, which significantly outperformed traditional methods in the ImageNet competition using deep convolutional network. Subsequently, He et al. (2016) introduced ResNet, which addressed the degradation problem in training deep network by incorporating residual blocks, significantly improving model performance. In the field of natural language proces...

## nrRkAAAufl

- gold_decision: `accept`
- old_chars: 800
- new_chars: 2400
- cleaned_wrapper: `True`
- contains_method: `False`
- contains_results: `True`
- contains_conclusion: `True`
- contains_table_or_figure: `True`
- snippet_sources: `['abstract', 'results', 'table_or_figure', 'conclusion']`

### old_first_800_preview

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'. --- BEGIN PAPER --- \title{Constraint-Conditioned Actor-Critic for Offline Safe Reinforcement Learning} \begin{abstract} Offline safe reinforcement learning (OSRL) aims to learn policies with high rewards while satisfying safety constraints solely from data collected offline. However, the learned policies often struggle to handle states and actions that are not present or out-of-distribution (OOD) from the offline dataset, which can result in violation of the safety constraints or overly conservative behaviors during their online deployment. Moreover, many existing methods are

### new_context_preview

[abstract] \title{Constraint-Conditioned Actor-Critic for Offline Safe Reinforcement Learning} \begin{abstract} Offline safe reinforcement learning (OSRL) aims to learn policies with high rewards while satisfying safety constraints solely from data collected offline. However, the learned policies often struggle to handle states and actions that are not present or out-of-distribution (OOD) from the offline dataset, which can result in violation of the safety constraints or overly conservative behaviors during their online deployment. Moreover, many existing methods are unable to learn policies that can adapt to varying constraint thresholds. To address these challenges, we propose constraint-conditioned [results] tate-action pairs and detecting OOD data, respectively. We demonstrate that these components can be used to effectively regularize the learning of both the critics and the actor. • We conduct comprehensive experiments to show that (i) CCAC outperforms state-of-the-art baselines both in safety and task performance by a large margin, and (ii) CCAC can achieve high rewards while generalizing to varying constraint thresholds without re-training the policy. \section{2 RELATED WO...

## IdAyXxBud7

- gold_decision: `accept`
- old_chars: 800
- new_chars: 2400
- cleaned_wrapper: `True`
- contains_method: `False`
- contains_results: `True`
- contains_conclusion: `True`
- contains_table_or_figure: `True`
- snippet_sources: `['abstract', 'results', 'table_or_figure', 'conclusion']`

### old_first_800_preview

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'. --- BEGIN PAPER --- \title{DynAlign: Unsupervised Dynamic Taxonomy Alignment for Cross-Domain Segmentation} \begin{abstract} Current unsupervised domain adaptation (UDA) methods for semantic segmentation typically assume identical class labels between the source and target domains. This assumption ignores the label-level domain gap, which is common in real-world scenarios, and limits their ability to identify finer-grained or novel categories without requiring extensive manual annotation. A promising direction to address this limitation lies in recent advancements in foundatio

### new_context_preview

[abstract] \title{DynAlign: Unsupervised Dynamic Taxonomy Alignment for Cross-Domain Segmentation} \begin{abstract} Current unsupervised domain adaptation (UDA) methods for semantic segmentation typically assume identical class labels between the source and target domains. This assumption ignores the label-level domain gap, which is common in real-world scenarios, and limits their ability to identify finer-grained or novel categories without requiring extensive manual annotation. A promising direction to address this limitation lies in recent advancements in foundation models, which exhibit strong generalization abilities due to their rich prior knowledge. However, these models often struggle with doma [results] lign generates accurate predictions in a new target label space without requiring any manual annotations, allowing seamless adaptation to new taxonomies through either model retraining or direct inference. Experiments on the GTA $\rightarrow$ IDD and GTA$\rightarrow$ Mapillary benchmarks validate the effectiveness of our approach, achieving a significant improvement over existing methods. \end{abstract} \section{1 INTRODUCTION } Semantic segmentation is a crucial computer v...

