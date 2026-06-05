# Support Quality Decision Simulation

Offline diagnostic simulations only. These are not runtime decision rules.

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids | wrongly_flipped_reject_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | 0.5 | 0.3333 | 0.0 | 1.0 | 0 |  |  |  |
| sim_a_abstract_only_excluded | 0.625 | 0.5636 | 0.25 | 1.0 | 2 |  | VEJzjAvaIy,pOq9vDIYev |  |
| sim_b_non_abstract_support_ge1 | 0.6875 | 0.6537 | 0.375 | 1.0 | 3 |  | VEJzjAvaIy,pOq9vDIYev,giU9fYGTND |  |
| sim_c_independent_groups_ge2 | 0.75 | 0.7333 | 0.5 | 1.0 | 4 |  | VEJzjAvaIy,pOq9vDIYev,giU9fYGTND,cpGPPLLYYx |  |
| sim_d_empirical_support_for_empirical_claims | 0.625 | 0.5636 | 0.25 | 1.0 | 2 |  | VEJzjAvaIy,pOq9vDIYev |  |
| sim_e_method_plus_result_combination | 0.625 | 0.5636 | 0.25 | 1.0 | 2 |  | VEJzjAvaIy,pOq9vDIYev |  |
| sim_f_criterion_grounded_accept_signal | 0.625 | 0.5636 | 0.25 | 1.0 | 2 |  | pOq9vDIYev,giU9fYGTND |  |
