# Review Issue Case Table

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_101215.jsonl`
- verified review issue cases: `3`
- quote-grounded cases: `0`
- obligation-grounded cases: `3`

| paper_id | bucket | issue_type | claim_id | missing/mismatch | inventory count | inventory sources | verification basis | inventory/quote locator | inventory/quote | claim anchor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XyB4VvF01X | obligation_grounded_review_issue | missing_ablation | claim-1 | ablation study isolating hierarchical representation component | 4 | verified_support_inventory, paper_text_inventory | claim_anchor_locatable_and_reviewer_candidate_specific_missing_item_with_verified_inventory | Figure 4 | Figure 4: Detailed Graph2Tac model architecture, composed of a definition task and prediction task. | Graph2Tac introduces a novel method for learning hierarchical representations of mathematical concepts from Coq definitions to improve tactic selection for unseen theorems. |
| QAgwFiIY4p | obligation_grounded_review_issue | efficiency_cost_gap | claim-2 | quantitative parameter count or computational cost comparison table for PST versus baselines | 1 | reviewer_candidate_observed_inventory | claim_anchor_locatable_and_reviewer_candidate_specific_missing_item_with_verified_inventory | Comparison (Results/Setup section) | Our PST uses fewer or comparable parameters than baselines across all datasets. | The proposed method achieves competitive or superior empirical performance on specific graph learning tasks compared to baseline GNNs. |
| mHv6wcBb0z | obligation_grounded_review_issue | method_support_gap | claim-1 | concrete specification of the noise type, distribution, and magnitude in NR-DCCA | 4 | verified_support_inventory, paper_text_inventory | claim_anchor_locatable_and_reviewer_candidate_specific_missing_item_with_verified_inventory | Section: Method | \subsection{Method} Based on the discussions in previous sections, we present NR-DCCA, which makes use of the noise regularization approach to prevent model collapse in DCCA. | The paper proposes NR-DCCA to prevent model collapse in DCCA via a noise regularization mechanism. |
