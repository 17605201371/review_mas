# Review Issue Case Table

- run: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api2_r8t600_tok1536_20260627_162459.jsonl`
- verified review issue cases: `2`
- quote-grounded cases: `0`
- obligation-grounded cases: `2`
- reviewer-candidate cases: `0`
- claim-obligation fallback cases: `2`

| paper_id | bucket | issue_type | claim_id | source | candidate id | missing/mismatch | inventory count | inventory sources | verification basis | inventory/quote locator | inventory/quote | claim anchor |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| QAgwFiIY4p | obligation_grounded_review_issue | efficiency_cost_gap | claim-2 | claim_obligation |  | parameter measurement under the claimed setting | 1 | verified_support_inventory | claim_anchor_locatable_and_auditable_expectation_with_verified_inventory | Table/Figure caption: Results on graph property prediction tasks. | \caption{Results on graph property prediction tasks.}\label{tab::zinc} | The conversion method enables using set encoders to learn from graphs, significantly expanding the design space of GNNs, and is broadly adaptable to both small and large graphs with comparable or better parameter effi... |
| TPAj63ax4Y | obligation_grounded_review_issue | missing_baseline | claim-3 | claim_obligation |  | same-setting comparison against LAVT | 2 | paper_text_inventory | claim_anchor_locatable_and_auditable_expectation_with_verified_inventory | paper inventory #4 | In our experiments, using only the first two steps (zero-shot segment and select) outperforms other zero-shot baselines by as much as 16.5\%, while our full method improves upon th | The proposed weakly-supervised method bridges the performance gap with fully-supervised baselines like LAVT. |
