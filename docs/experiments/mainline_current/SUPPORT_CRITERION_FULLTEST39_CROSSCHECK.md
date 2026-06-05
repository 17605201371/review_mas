# Support + Criterion Fulltest39 Cross-Check

This cross-check reuses existing `decision_hygiene_view_v1_fulltest39_4b.jsonl`; it does not rerun a model and does not change runtime.

## Aggregate Comparison

| dataset | rows | real_strong | non_abstract | empirical | method | independent_groups | claims_2plus_independent | fallback_or_unbound_strong |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binding_v1_mixed16 | 16 | 13 | 9 | 2 | 7 | 12 | 3 | 0 |
| fulltest39_crosscheck | 39 | 20 | 17 | 8 | 9 | 20 | 1 | 0 |

## Simulation Comparison

| dataset | simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binding_v1_mixed16 | original | 0.5 | 0.3333 | 0.0 | 1.0 | 0 |  |  |
| binding_v1_mixed16 | sim_b_non_abstract_support_ge1 | 0.6875 | 0.6537 | 0.375 | 1.0 | 3 |  | VEJzjAvaIy,pOq9vDIYev,giU9fYGTND |
| binding_v1_mixed16 | sim_c_independent_groups_ge2 | 0.75 | 0.7333 | 0.5 | 1.0 | 4 |  | VEJzjAvaIy,pOq9vDIYev,giU9fYGTND,cpGPPLLYYx |
| binding_v1_mixed16 | sim_f_criterion_grounded_accept_signal | 0.625 | 0.5636 | 0.25 | 1.0 | 2 |  | pOq9vDIYev,giU9fYGTND |
| fulltest39_crosscheck | original | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | XyB4VvF01X,QAgwFiIY4p,TPAj63ax4Y,kam84eEmub |  |
| fulltest39_crosscheck | sim_b_non_abstract_support_ge1 | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | XyB4VvF01X,QAgwFiIY4p,TPAj63ax4Y,kam84eEmub |  |
| fulltest39_crosscheck | sim_c_independent_groups_ge2 | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | XyB4VvF01X,QAgwFiIY4p,TPAj63ax4Y,kam84eEmub |  |
| fulltest39_crosscheck | sim_f_criterion_grounded_accept_signal | 0.6667 | 0.4 | 0.0 | 0.8667 | 4 | NnExMNiTHw,QAgwFiIY4p,kam84eEmub,N0isTh3rml |  |

## Interpretation

- `binding_v1_mixed16` shows that independent/non-abstract support can recover accept-like cases without false accepts in the fixed balanced subset.

- `fulltest39_crosscheck` does not recover additional accepts with the same simple simulations and still has false accepts, so the rule should not be promoted into runtime final decision.

- The safe next cut is still Evidence Context Selection v2 / claim-evidence formation, not a hard accept/reject threshold. The system needs more stable non-abstract, independent support on gold-accept samples before final-view filtering can be trusted.
