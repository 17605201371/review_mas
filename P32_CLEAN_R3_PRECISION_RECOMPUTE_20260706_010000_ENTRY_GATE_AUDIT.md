# P31.6 Entry Gate Audit

- dashboard: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000_HARDNEG20_DASHBOARD.json`
- review issue cases: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000_REVIEW_ISSUE_CASE_TABLE.json`
- recovery cases: `P32_CLEAN_R3_PRECISION_RECOMPUTE_20260706_010000_RECOVERY_CASE_TABLE.json`
- machine gate: **PASS**
- manual gate: **REQUIRED**

## Machine Checks

| check | actual | required | status |
|---|---:|---:|---|
| `dashboard_protection_passed` | True | True | PASS |
| `critique_direct_verified_cluster_count` | 6 | >= 3 | PASS |
| `candidate_menu_item_verified_count` | 6 | >= 2 | PASS |
| `case_table_critique_origin_cluster_count` | 6 | >= 3 | PASS |
| `case_table_cluster_count_matches_rows_minus_duplicates` | 9 | 9 | PASS |
| `dashboard_case_cluster_count_match` | 9 | 9 | PASS |
| `dashboard_recomputed_cluster_count_match` | 9 | 9 | PASS |
| `dashboard_quote_merged_cluster_count_not_above_system` | 9 | <= 9 | PASS |
| `dashboard_origin_cluster_counts_sum` | 9 | 9 | PASS |
| `negative_evidence_unlinked_to_flaw` | 0 | 0 | PASS |
| `positive_or_neutral_negative_candidate_count` | 0 | 0 | PASS |
| `negative_grounding_conflict_count` | 0 | 0 | PASS |

## Critique-Origin Clusters For Manual Audit

| paper | type | target | claims | missing/mismatch | inventory anchor |
|---|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | claim-1, claim-2 | graph control module; component-isolation ablation for with a graph control module | Claim-matched evidence excerpt #1 |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | claim-3 | same-setting comparison against paper-named GPT-4 baseline | Table/Figure caption: Basic statistics for OrcaData. |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | claim-1, claim-2 | acceptance prediction head | Section: SpecDec++: Theory and Algorithm |
| QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | claim-1 | y coordinates without information loss | Section: Conclusion |
| YXn76HMetm | missing_baseline | paper-named_pixelpick_baseline | claim-3 | same-setting comparison against paper-named PixelPick baseline; same-setting comparison against p... | Table: results table |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | claim-1, claim-3, claim-4 | runtime, memory, parameter, FLOP, hardware, or compute-cost measurement for the efficiency claim | Section: Method |

## Critique Selected-Menu Attribution

| paper | type | target | menu ids | mode |
|---|---|---|---|---|
| GE6iywJtsV | missing_ablation | graph_control_module | rim-c2-ma-graph-control-module-2 | critique_direct_verified_cluster |
| NnExMNiTHw | missing_ablation | acceptance_prediction_head | rim-c1-ma-acceptance-prediction-head | critique_direct_verified_cluster |
| HPuLU6q7xq | missing_baseline | paper-named_gpt-4_baseline | rim-c3-mb-same-setting-comparison-against | critique_direct_verified_cluster |
| fGXyvmWpw6 | efficiency_cost_gap | efficiency_resource_measurement | rim-c3-ec-runtime-memory-parameter-flop-ha | critique_direct_verified_cluster |
| QAgwFiIY4p | missing_ablation | coordinates_without_information_loss | rim-c1-ma-y-coordinates-without-informatio | critique_direct_verified_cluster |

## Selected-Menu Failure Details

| paper | stage | reason | type | target | locator |
|---|---|---|---|---|---|
| uOrfve3prk | inventory_anchor | observed_inventory_missing | evaluation_protocol_risk | protocol reporting protocol or comparability setting | paper inventory #2 |
| 9zEBK3E9bX | counterevidence | full_text_evaluation_or_scope_counterevidence | scope_overclaim | held-out or coverage evaluation for fine-tuning | paper inventory #1 |
| WpXq5n8yLb | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | recurrent draft model | paper component inventory #1 |
| a6SntIisgg | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | feature dependencies by self-attention mechanism | paper component inventory #1 |
| TPAj63ax4Y | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | zero-shot choice module module | paper inventory #10 |
| mHv6wcBb0z | counterevidence | missing_ablation_counterevidence_in_claim_or_inventory | missing_ablation | ablation isolating uses noise regularization module | paper inventory #1 |
| xUe1YqEgd6 | counterevidence | full_text_evaluation_or_scope_counterevidence | missing_robustness_or_generalization | held-out or coverage evaluation for FlyingThings3D | paper inventory #1 |

## Red-Flag Scan

| category | term | paper | type | missing/mismatch |
|---|---|---|---|---|
| author_limitation | `limitation` | ye3NrNrYOY | missing_ablation | fixed module; ablation isolating encoder/backbone or its named component; ablation isolating aspe... |

## Notes

- Machine PASS is not paper-ready approval; manual A/B audit of the listed Critique-origin clusters is still required.
- The red-flag scan is lexical only and should be treated as triage, not a verifier.
- P32 entry remains blocked if the machine gate fails or manual audit finds external-baseline, retrieval/context, author-limitation, or other false positives.
