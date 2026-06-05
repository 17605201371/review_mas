# Borderline Positive Case Review v1

## 汇总

| bucket | count |
| --- | --- |
| reject_false_accept_risk_no_hard_negative | 8 |
| reject_false_accept_risk_unresolved_heavy | 3 |
| gold_accept_but_unresolved_heavy | 2 |
| reject_false_accept_risk_with_ungrounded_flaw | 2 |

| gold | count |
| --- | --- |
| reject | 13 |
| accept | 2 |

## ye3NrNrYOY (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=2, meta_burden=4
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Figure 2(b) shows TCMT achieves better outcomes with fewer epochs than TCMT-FT where all parts are updated.
  - claim-1/method_or_approach: Method section proposes TCMT assuming distribution discrepancies stem from an auxiliary variable.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Insufficient Evidence for Core Claims", "description": "The prov
- top unresolved:
  - Is the full paper text available to complete the abstract and methodology sections?
  - The abstract is incomplete; the specific challenge mentioned ('base and ...') is cut off.
  - Specific quantitative accuracy gains in Table 4 are not fully legible in the excerpt.

## uOrfve3prk (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=3, meta_burden=3
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Framework proposes two metrics: intervention success rate and coherence-intervention tradeoff.
  - claim-1/method_or_approach: Authors view intervention as a fundamental goal of interpretability.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Claims", "description": "Clai
- top unresolved:
  - The abstract is cut off mid-sentence; how does the paper propose to unify interpretability and control?
  - What specific evaluation via intervention methods are proposed?
  - Full results for intervention success rates and coherence-intervention tradeoffs are truncated and cannot be fully verified.

## 9zEBK3E9bX (reject)

- bucket: `reject_false_accept_risk_unresolved_heavy`
- support: real=3, nonabstract=3, empirical=3, groups=3
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=8, meta_burden=3
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Figure 1(a) shows scalable performance improvement across datasets/tasks with varying pre-training data amounts.
  - claim-3/result_or_experiment: Figure 1(b) states SPOT delivers best performance among different pre-training methods on various datasets.
  - claim-3/result_or_experiment: Figure 1(b) shows SPOT achieves best performance across KITTI, nuScenes, and Waymo detection tasks.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Critical Data Truncation Prevents Validity Assessment", "descrip
- top unresolved:
  - What is the specific contribution of SPOT?
  - The abstract is cut off; the specific mechanism for alleviating annotation burden is missing.
  - The full introduction and methodology are not available to verify the 'occupancy prediction' approach.

## WpXq5n8yLb (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=2, meta_burden=5
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: ReDrafter accelerates Vicuna inference by up to 3.5x compared to autoregressive method on Nvidia H100 GPUs in MT-Bench.
  - claim-3/result_or_experiment: ReDrafter mitigates memory bottlenecks in TensorRT-LLM, achieving up to 2.3x speedup in resource-constrained environments.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Grounding for Core Architectural Claims", "des
- top unresolved:
  - The excerpt is truncated and does not contain the specific methodological details (RNN draft model, dynamic tree attention) or complete experimental results needed to extract verif
  - The abstract mentions 'three key' drivers but does not list them in the provided text.
  - The provided paper excerpt for 'Recurrent Drafter for Fast Speculative Decoding in Large Language Models' is truncated. Please provide the full text of the paper, including the com

## NnExMNiTHw (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=4, meta_burden=3
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Figure caption reports 7.2%, 11.1%, and 9.4% relative improvements on Alpaca, HumanEval, and GSM8K over baseline SpecDec.
  - claim-2/result_or_experiment: Figure caption reports 7.2%, 11.1%, and 9.4% relative improvements over baseline SpecDec on Alpaca, HumanEval, and GSM8K.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Incomplete Methodology Prevents Verification of Adaptive Mechani
- top unresolved:
  - The abstract is cut off; the full methodology and results are not visible yet.
  - The abstract text is truncated; full methodological details and ablation studies are missing to fully verify the acceptance prediction head's design.
  - The provided paper text is truncated (the abstract ends mid-sentence). Please provide the full text of the paper, including the complete abstract, introduction, methodology, and re

## cklg91aPGk (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=3, meta_burden=1
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/conclusion_or_discussion: PROP achieves competitive results without training, falling behind DGI by only 0.29% on ogbn-arxiv while offering higher efficiency.
  - claim-2/result_or_experiment: GCL weights show uniform smoothing resembling a normal distribution, unlike SL weights which have substantial variance and leptokurtic shape.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Empirical Grounding for Performance Claims", "descriptio
- top unresolved:
  - Do the provided results tables and figures fully support the competitive performance claim?
  - Is the characterization of GCL weights as 'overly generalized' empirically validated in the full paper?
  - Check whether this weakness is explicitly grounded in the paper text.

## QAgwFiIY4p (reject)

- bucket: `reject_false_accept_risk_unresolved_heavy`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=5, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/method_or_approach: Method converts graph to point set via symmetric rank decomposition of augmented adjacency matrix A+D into QQ^T.
  - claim-3/result_or_experiment: Extensive experiments verify PST outperforms all baselines on QM9 dataset for graph property prediction.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Ambiguity in 'Lossless' Graph-to-Set Conversion Mechanism", "des
- top unresolved:
  - What is the specific definition of the 'graph-to-set conversion' method?
  - How does this method compare to existing GNNs in terms of performance and expressivity?
  - Full experimental results and ablation studies are missing to verify performance claims.

## KI9NqjLVDT (accept)

- bucket: `gold_accept_but_unresolved_heavy`
- support: real=3, nonabstract=3, empirical=3, groups=3
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=6, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Extensive evaluation on 12 benchmark datasets shows ReMasker performs on par with or outperforms 13 methods, with advantages increasing at high missingness ratios (e.g., 0.7).
  - claim-1/result_or_experiment: Theoretical analysis finds ReMasker encourages learning missingness-invariant representations that are insensitive to missing values.
  - claim-2/result_or_experiment: Extensive evaluation on 12 benchmark datasets shows performance on par with or outperforming 13 methods, especially at high missing ratios (0.7).
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Missingness-Invariance", "descript
- top unresolved:
  - What is the full abstract and introduction of the paper?
  - What specific masking strategy does ReMasker employ beyond random masking?
  - How does the theoretical explanation for missingness-invariance specifically manifest in the model architecture?

## TPAj63ax4Y (reject)

- bucket: `reject_false_accept_risk_with_ungrounded_flaw`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=1, targetless_unresolved=6, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: Outperforms zero-shot by 19% and weakly-supervised by up to 26% on RefCOCO, RefCOCO+, and RefCOCOg.
  - claim-1/result_or_experiment: Outperforms zero-shot by 19% and weakly-supervised by up to 26% on RefCOCO, RefCOCO+, and RefCOCOg.
- top flaws:
  - critical/candidate/: Critical Data Gap: Incomplete Paper Text Prevents Verification
- top unresolved:
  - What is the full abstract and introduction of the paper?
  - What are the specific weakly-supervised and zero-shot approaches being compared?
  - Please provide the complete text of the paper, including the full abstract, introduction, methodology, and results sections, as the current input cuts off mid-sentence in the abstr

## xUe1YqEgd6 (reject)

- bucket: `reject_false_accept_risk_unresolved_heavy`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=5, meta_burden=1
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-3/result_or_experiment: Comparative experiments conducted on four datasets: DAVIS 2016, SegTrackV2, FBMS, and DAVIS2017-motion.
  - claim-2/method_or_approach: The method models long-term temporal evolution of motion model parameters using B-splines.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Quantitative Comparison to Frame-by-Frame Baselines", "d
- top unresolved:
  - What are the specific claims made by the authors regarding their method's performance and novelty?
  - Does the paper provide quantitative results comparing the 'one go' approach to frame-by-frame baselines?
  - What are the specific quantitative results on the four benchmarks?

## jVEoydFOl9 (accept)

- bucket: `gold_accept_but_unresolved_heavy`
- support: real=4, nonabstract=4, empirical=2, groups=3
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=7, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: Method generalizes to 50+ different KGs with sizes of 1,000--120,000 nodes and 5K--1M edges.
  - claim-3/method_or_approach: Approach uses relative entity and relation representations to generalize to new entities and relations.
  - claim-2/result_or_experiment: Method generalizes to 50+ KGs; zero-shot performance exceeds strong supervised baselines by up to 300%.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Claims", "description": "The
- top unresolved:
  - What is the full abstract and introduction of the paper?
  - What are the specific claims made about foundation models for KGs?
  - The full abstract and detailed methodology are missing, preventing verification of the core contribution.

## YXn76HMetm (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=2, meta_burden=1
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: HALO sets new SOTA on benchmarks: +3.3% on GTA→CS, +4.2% on SYNTHIA→CS, +2.9% on CS→ACDC.
  - claim-2/result_or_experiment: First AL method surpassing supervised domain adaptation baseline using only 5% labels (GTA→CS).
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for SOTA and Novelty Claims", "descrip
- top unresolved:
  - How does the novel stability technique specifically function and what is its impact on convergence?
  - Check whether this weakness is explicitly grounded in the paper text.

## KOUAayk5Kx (reject)

- bucket: `reject_false_accept_risk_with_ungrounded_flaw`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=1, targetless_unresolved=9, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: Figure 1(b) shows validation accuracy of Arc A degrading when training Arc B, demonstrating multi-model forgetting.
  - claim-1/result_or_experiment: Figure 1(b) shows validation accuracy of ArcA degrading when training ArcB, demonstrating multi-model forgetting.
- top flaws:
  - critical/candidate/: Incomplete Evidence Base Prevents Flaw Analysis
- top unresolved:
  - What is the specific definition of 'multi-model forgetting' in this context?
  - How does Orthogonal Gradient Learning technically address this issue?
  - What are the quantitative results compared to baselines?

## WLgbjzKJkk (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=1, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=3, meta_burden=2
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-2/result_or_experiment: Method evaluated on DanceTrack, BDD100K, and MOT17 achieving superior performance.
  - claim-1/method_or_approach: Introduces coopetition label assignment and one-to-set matching with shadow queries.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Lack of Grounded Evidence for Core Methodological Claims", "desc
- top unresolved:
  - How does the 'Coopetition Label Assignment' specifically differ from existing methods?
  - What are the results of the proposed method compared to tracking-by-detection baselines?
  - Quantitative comparison details against specific baselines are not fully visible in the excerpt.

## LieTse3fQB (reject)

- bucket: `reject_false_accept_risk_no_hard_negative`
- support: real=2, nonabstract=2, empirical=2, groups=2
- blockers: grounded_major=0, ungrounded_flaw=0, targetless_unresolved=3, meta_burden=1
- lifecycle: `accept_like` / real_nonabstract_support_without_grounded_blocker
- top evidence:
  - claim-1/result_or_experiment: Figure 1 shows GaussianFocus surpassing 3DGS in scenes with slender geometries, intricate details, and lighting effects.
  - claim-2/result_or_experiment: Figure 7 presents an ablation study on the Garden scene comparing results with and without the Gaussian Patch Attention Enhancement Strategy.
- top flaws:
  - minor/downgraded/fallback-extraction: { "flaw_candidates": [ { "flaw_id": "flaw-1", "title": "Overgeneralization of Performance Claims", "description": "Claim
- top unresolved:
  - Are the visual improvements in Figure 1 quantified by specific metrics?
  - Does the ablation study in Figure 7 confirm the necessity of the patch attention strategy?
  - Check whether this weakness is explicitly grounded in the paper text.
