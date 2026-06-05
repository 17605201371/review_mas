# Soft Focus v2 Borderline / False-Reject Casebook

本表覆盖全部 gold accept、accept_like 与 borderline_positive。用途是判断哪些样本只差 method/soundness evidence，哪些样本仍被 hard-negative burden 阻断。

| paper_id | gold | runtime | view | real | empirical | method | independent | novelty | soundness | empirical_rating | family | missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hj323oR3rw | accept | reject | not_assessable | 0 | 0 | 0 | 0 | not_assessable | not_assessable | not_assessable | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| 9zEBK3E9bX | reject | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive |
| XyB4VvF01X | reject | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive |
| GE6iywJtsV | reject | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| QAAsnSRwgu | accept | reject | borderline_insufficient | 1 | 0 | 1 | 1 | positive | positive | not_assessable | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_empirical_support,independent_lt3,unresolved_gt4,empirical_not_positive |
| X41c4uB4k0 | accept | reject | reject_like | 1 | 1 | 0 | 1 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| NnExMNiTHw | reject | accept | borderline_positive | 3 | 3 | 0 | 3 | not_assessable | not_assessable | positive | method_soundness_gap | no_method_support,novelty_not_positive,soundness_not_positive |
| gzqrANCF4g | accept | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| QAgwFiIY4p | reject | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | method_soundness_gap | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive |
| KI9NqjLVDT | accept | reject | borderline_insufficient | 1 | 0 | 1 | 1 | positive | positive | not_assessable | support_depth_gap | real_strong_lt3,nonabstract_lt3,no_empirical_support,independent_lt3,empirical_not_positive |
| 1HCN4pjTb4 | accept | reject | borderline_insufficient | 1 | 0 | 1 | 1 | positive | positive | not_assessable | support_depth_gap | real_strong_lt3,nonabstract_lt3,no_empirical_support,independent_lt3,empirical_not_positive |
| LebzzClHYw | accept | reject | accept_like | 3 | 2 | 1 | 3 | positive | positive | positive | passes_or_other |  |
| BXY6fe7q31 | accept | reject | borderline_positive | 4 | 4 | 0 | 4 | not_assessable | not_assessable | positive | method_soundness_gap | no_method_support,novelty_not_positive,soundness_not_positive |
| jVEoydFOl9 | accept | reject | reject_like | 1 | 1 | 0 | 1 | not_assessable | negative | negative | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| KOUAayk5Kx | reject | reject | borderline_positive | 2 | 2 | 0 | 2 | not_assessable | not_assessable | positive | hard_negative_burden | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| ZHr0JajZfH | reject | reject | borderline_positive | 3 | 2 | 1 | 3 | positive | positive | positive | hard_negative_burden | unresolved_gt4 |
