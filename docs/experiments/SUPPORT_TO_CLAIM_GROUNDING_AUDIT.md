# Support-to-Claim Grounding Audit

**运行行为是否改变**：否。

## 1. strong support 绑定对象统计

| metric | count |
|---|---|
| final_strong_positive_fallback_claim | 9 |
| final_strong_positive_real_claim | 45 |
| final_strong_positive_supported_claim | 12 |
| final_strong_positive_total | 54 |
| final_strong_positive_unbound | 0 |
| final_strong_positive_unsupported_claim | 33 |
| support_to_real_claim_grounding_rate | 0.833 |

## 2. 按 gold decision 分组

| gold | strong_total | real_claim | fallback_claim | unsupported_claim | supported_claim | real_claim_rate |
|---|---|---|---|---|---|---|
| accept | 18 | 16 | 2 | 14 | 2 | 0.889 |
| reject | 36 | 29 | 7 | 19 | 10 | 0.806 |

## 3. FALLBACK_BOUND_SUPPORT_CASES

| run | paper_id | gold | claim_id | evidence_id | source | evidence_preview | risky_to_count |
|---|---|---|---|---|---|---|---|
| 4b_focus | hj323oR3rw | accept | claim-fallback-1 | evidence-1 | Abstract | The paper title is 'Towards Robust Multimodal Open-set Test-time Adaptation via Adaptive Entropy-aware Optimization'. The abstract states: 'Open-set test-time adaptation (OSTTA) aims to adapt a source pre-trained model online to an unlabele | True |
| 4b_focus | TPAj63ax4Y | reject | claim-fallback-1 | evidence-1 | Abstract | The paper title is 'Segment, Select, Correct: A Framework for Weakly-Supervised Referring Segmentation' and the abstract states: 'Referring Image Segmentation (RIS) -- the problem of identifying objects in images through natural language se | True |
| 4b_focus | TPAj63ax4Y | reject | claim-fallback-1 | evidence-2 | Abstract | The abstract explicitly states the paper's goal: 'To bridge the performance gap without [supervised learning]...' (text cuts off but context implies the proposed framework aims to do so). | True |
| 4b_focus | aTBE70xiFw | reject | claim-fallback-1 | evidence-1 | Abstract | The paper introduces 'Polar Transformers' specifically for 'Joint Denoising of Cryo-EM Projection Images'. The abstract states that while DNNs have limits on noise levels, cryo-EM datasets contain 'hundreds of thousands of projections of th | True |
| 4b_focus | aTBE70xiFw | reject | claim-fallback-1 | evidence-2 | Abstract | The text explicitly mentions that 'Deep neural networks (DNNs) have proven powerful for denoising individual images, but there is a limit to the noise level they can handle.' This establishes the motivation for the new approach. | True |
| 4b_focus | KOUAayk5Kx | reject | claim-fallback-1 | evidence-1 | Abstract | The abstract explicitly states: 'However, there is an issue of multi-model forgetting about supernet training in one-shot NAS that some weights of the previously well-trained architecture will be overwritten by that of the newly sampled arc | True |
| 4b_mixed_v2 | GSckuQMzBG | reject | claim-fallback-1 | evidence-1 | Abstract | The abstract states: 'While the field of inverse graphics has been witnessing continuous growth, techniques devised thus far predominantly focus on learning individual scene representations. In contrast, learning large sets of scenes has be | True |
| 4b_mixed_v2 | GSckuQMzBG | reject | claim-fallback-1 | evidence-2 | Abstract | The abstract introduces the proposed solution: 'We introduce a framework termed Scaled Inverse Graphics...' | True |
| 4b_mixed_v2 | IdAyXxBud7 | accept | claim-fallback-1 | evidence-1 | Abstract | The abstract states: 'Current unsupervised domain adaptation (UDA) methods for semantic segmentation typically assume identical class labels between the source and target domains. This assumption ignores the label-level domain gap, which is | True |

## 4. 判断

- **fallback-bound support** 不应直接作为 accept 证据；它可能是真证据，也可能是 fallback 伪证据。
- 如果正向 support 多数绑定 fallback claim，下一步应是 Support-to-Real-Claim Grounding；如果 strong support 总量本身很低，最早断点仍在输入/抽取层。
