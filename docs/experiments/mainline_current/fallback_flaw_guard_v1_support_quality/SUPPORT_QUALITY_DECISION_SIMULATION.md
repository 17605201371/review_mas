# Support Quality Decision Simulation

Offline diagnostic simulations only. These are not runtime decision rules.

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids | wrongly_flipped_reject_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 |  |  |  |
| sim_a_abstract_only_excluded | 0.7436 | 0.5647 | 0.2222 | 0.9 | 5 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH |
| sim_b_non_abstract_support_ge1 | 0.7436 | 0.5647 | 0.2222 | 0.9 | 5 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH |
| sim_c_independent_groups_ge2 | 0.7436 | 0.5647 | 0.2222 | 0.9 | 5 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 | uOrfve3prk,9zEBK3E9bX,ZHr0JajZfH |
| sim_d_empirical_support_for_empirical_claims | 0.7692 | 0.5846 | 0.2222 | 0.9333 | 4 | 9zEBK3E9bX,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 | 9zEBK3E9bX,ZHr0JajZfH |
| sim_e_method_plus_result_combination | 0.7692 | 0.5237 | 0.1111 | 0.9667 | 2 | ZHr0JajZfH | LebzzClHYw | ZHr0JajZfH |
| sim_f_criterion_grounded_accept_signal | 0.5897 | 0.4935 | 0.3333 | 0.6667 | 13 | ye3NrNrYOY,uOrfve3prk,9zEBK3E9bX,GE6iywJtsV,WpXq5n8yLb,cklg91aPGk,fGXyvmWpw6,KOUAayk5Kx,ZHr0JajZfH,LieTse3fQB | X41c4uB4k0,LebzzClHYw,BXY6fe7q31 | ye3NrNrYOY,uOrfve3prk,9zEBK3E9bX,GE6iywJtsV,WpXq5n8yLb,cklg91aPGk,fGXyvmWpw6,KOUAayk5Kx,ZHr0JajZfH,LieTse3fQB |
