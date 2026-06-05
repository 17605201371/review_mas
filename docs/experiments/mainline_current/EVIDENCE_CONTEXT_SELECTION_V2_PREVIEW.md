# Evidence Context Selection v2 Preview

本预览只检查 context 选择，不跑模型。v2 优先真实 section header，避免把 abstract 里的普通 results/table 词误记为结果段。

## hj323oR3rw

- mode: `section_aware_v2`

- sources: `['abstract', 'method', 'results', 'table_or_figure', 'conclusion']`

- contains_method/results/table/conclusion: `True/True/True/True`

- chars: `2400`

### old first 800

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'.  --- BEGIN PAPER --- \title{Towards Robust Multimodal Open-set Test-time Adaptation via Adaptive Entropy-aware Optimization}  \begin{abstract} Test-time adaptation (TTA) has demonstrated significant potential in addressing distribution shifts between training and testing data. Open-se

### new context preview

[abstract] \title{Towards Robust Multimodal Open-set Test-time Adaptation via Adaptive Entropy-aware Optimization} \begin{abstract} Test-time adaptation (TTA) has demonstrated significant potential in addressing distribution shifts between training and testing data. Open-set test-time adaptation (OSTTA) aims to adapt a source pre-trained model online to an unlabeled target domain that contains unknown classes. This task becomes more challenging when multiple modalities are involved. Existing methods have primarily focused on unimodal OSTTA, often filtering out low-confidence samples without addressing the complexities of multimodal data. In this work, we present Adaptive Entropy-awa  [method] ding OSTTA (Lee et al., 2023) and UniEnt (Gao et al., 2024), have been developed. However, OSTTA assumes that confidence values for unknown samples are lower in the adapted model than in the original model, which may not hold in Multimodal Open-Set TTA (MM-OSTTA) settings. UniEnt relies heavily on the quality of the embedding space to accurately detect unknown classes. The goal of MM-OSTTA is to adapt a pre-trained multimodal model from the source domain to a previously unseen target domain wi

## KI9NqjLVDT

- mode: `section_aware_v2`

- sources: `['abstract', 'method', 'results', 'table_or_figure', 'conclusion']`

- contains_method/results/table/conclusion: `True/True/True/True`

- chars: `2400`

### old first 800

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'.  --- BEGIN PAPER --- \title{ReMasker: Imputing Tabular Data with Masked Autoencoding}  \begin{abstract}  We present \model, a new method of imputing missing values in tabular data by extending the masked autoencoding framework. %conduct a pilot study of exploring transformers in the t

### new context preview

[abstract] \title{ReMasker: Imputing Tabular Data with Masked Autoencoding} \begin{abstract} We present \model, a new method of imputing missing values in tabular data by extending the masked autoencoding framework. %conduct a pilot study of exploring transformers in the task of tabular data imputation. Compared with prior work, \model is both {\em simple} -- besides the missing values (\mie, naturally masked), we randomly ``re-mask'' another set of values, optimize the autoencoder by reconstructing this re-masked set, and apply the trained model to predict the missing values; and {\em effective} -- with extensive evaluation on benchmark datasets, we show that \model performs on par  [method] imputation methods can be roughly categorized as either discriminative or generative. The discriminative methods~\cite{missforest,mice,miracle} often specify a univariable model for each feature conditional on all others and perform cyclic regression over each target variable until convergence. Recent work has also explored adaptively selecting and configuring multiple discriminative imputers~\cite{hyperimpute}. The generative methods either implicitly train imputers as generators within the G

## jVEoydFOl9

- mode: `section_aware_v2`

- sources: `['abstract', 'method', 'results', 'table_or_figure', 'conclusion']`

- contains_method/results/table/conclusion: `True/True/True/True`

- chars: `2399`

### old first 800

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'.  --- BEGIN PAPER --- \title{Towards Foundation Models for Knowledge Graph Reasoning}  \begin{abstract}  Foundation models in language and vision have the ability to run inference on any textual and visual inputs thanks to the transferable representations such as a vocabulary of tokens

### new context preview

[abstract] \title{Towards Foundation Models for Knowledge Graph Reasoning} \begin{abstract} Foundation models in language and vision have the ability to run inference on any textual and visual inputs thanks to the transferable representations such as a vocabulary of tokens in language. Knowledge graphs (KGs) have different entity and relation vocabularies that generally do not overlap. The key challenge of designing foundation models on KGs is to learn such transferable representations that enable inference on any graph with arbitrary entity and relation vocabularies. In this work, we make a step towards such foundation models and present \method, an approach for learning universal  [method] om the original graph) capturing their interactions. Applying a graph neural network (GNN) with a \emph{labeling trick}~\citep{labeling_trick} over the graph of relations, \method obtains a unique \emph{relative} representation of each relation. The relation representations can then be used by any inductive learning method for downstream applications like KG completion. Since the method does not learn any graph-specific entity or relation embeddings nor requires any input entity or relation fea

## ZHr0JajZfH

- mode: `section_aware_v2`

- sources: `['abstract', 'method', 'results', 'table_or_figure', 'conclusion']`

- contains_method/results/table/conclusion: `True/True/True/True`

- chars: `2400`

### old first 800

[Instruction]: Review the following academic paper. Format requirements: Your review MUST include sections: # Summary, # Strengths, # Weaknesses, # Questions, and finally 'Decision Recommendation: [Accept/Reject]'.  --- BEGIN PAPER --- \title{A Simple Unified Uncertainty-Guided Framework for Offline-to-Online Reinforcement Learning}  \begin{abstract} Offline reinforcement learning (RL) provides a promising solution to learning an agent fully relying on a data-driven paradigm. However, constraine

### new context preview

[abstract] \title{A Simple Unified Uncertainty-Guided Framework for Offline-to-Online Reinforcement Learning} \begin{abstract} Offline reinforcement learning (RL) provides a promising solution to learning an agent fully relying on a data-driven paradigm. However, constrained by the limited quality of the offline dataset, its performance is often sub-optimal. Therefore, it is desired to further finetune the agent via extra online interactions before deployment. Unfortunately, offline-to-online RL can be challenging due to two main challenges: \textit{constrained exploratory behavior} and \textit{state-action distribution shift}. To this end, we propose a \textbf{S}imple \textbf{U}nif  [method] ucb}. The main idea here is to select those state-action pairs with both high value and high uncertainty for efficient exploration. We also propose an adaptive exploitation method to handle the state-action distribution shift by identifying and constraining OOD samples. The key insight is to leverage conservative offline RL objectives for high-uncertainty samples, and standard online RL objectives for low-uncertainty samples. This enables agents to smoothly adapt to changes in the state-action
