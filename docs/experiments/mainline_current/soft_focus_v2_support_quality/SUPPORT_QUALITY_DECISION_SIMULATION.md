# Support Quality Decision Simulation

Offline diagnostic simulations only. These are not runtime decision rules.

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids | wrongly_flipped_reject_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | NnExMNiTHw |  |  |
| sim_a_abstract_only_excluded | 0.6923 | 0.5667 | 0.3333 | 0.8 | 9 | uOrfve3prk,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 | uOrfve3prk,GE6iywJtsV,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH |
| sim_b_non_abstract_support_ge1 | 0.6923 | 0.5667 | 0.3333 | 0.8 | 9 | uOrfve3prk,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 | uOrfve3prk,GE6iywJtsV,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH |
| sim_c_independent_groups_ge2 | 0.6923 | 0.5667 | 0.3333 | 0.8 | 9 | uOrfve3prk,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 | uOrfve3prk,GE6iywJtsV,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH |
| sim_d_empirical_support_for_empirical_claims | 0.7179 | 0.5863 | 0.3333 | 0.8333 | 8 | GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 | GE6iywJtsV,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH |
| sim_e_method_plus_result_combination | 0.7692 | 0.5237 | 0.1111 | 0.9667 | 2 | ZHr0JajZfH | LebzzClHYw | ZHr0JajZfH |
| sim_f_criterion_grounded_accept_signal | 0.6154 | 0.5883 | 0.7778 | 0.5667 | 20 | ye3NrNrYOY,uOrfve3prk,GE6iywJtsV,WpXq5n8yLb,NnExMNiTHw,a6SntIisgg,cklg91aPGk,fGXyvmWpw6,QAgwFiIY4p,TPAj63ax4Y,KOUAayk5Kx,ZHr0JajZfH,LieTse3fQB | QAAsnSRwgu,X41c4uB4k0,gzqrANCF4g,KI9NqjLVDT,1HCN4pjTb4,LebzzClHYw,BXY6fe7q31 | ye3NrNrYOY,uOrfve3prk,GE6iywJtsV,WpXq5n8yLb,a6SntIisgg,cklg91aPGk,fGXyvmWpw6,QAgwFiIY4p,TPAj63ax4Y,KOUAayk5Kx,ZHr0JajZfH,LieTse3fQB |
