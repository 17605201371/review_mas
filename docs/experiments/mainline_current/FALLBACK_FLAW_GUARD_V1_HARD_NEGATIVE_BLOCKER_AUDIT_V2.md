# Hard-Negative Blocker Audit v2

宽松 support-quality / criterion-positive 规则的主要风险是把 gold reject 中的 result support 误当成 accept-like。high-precision 规则通过 method support、soundness/novelty positive 与 hard-negative blocker 同时约束，把这些风险样本挡回 reject。

| paper_id | runtime | support_quality | criterion_positive | high_precision | real | empirical | method | unresolved | major | novelty | soundness | empirical_rating | blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9zEBK3E9bX | reject | accept | accept | reject | 2 | 2 | 0 | 1 | 0 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive |
| QAgwFiIY4p | reject | accept | reject | reject | 2 | 2 | 0 | 4 | 2 | not_assessable | not_assessable | negative | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| TPAj63ax4Y | reject | accept | accept | reject | 2 | 1 | 1 | 5 | 3 | positive | positive | positive | real_strong_lt3,nonabstract_lt3,independent_lt3,unresolved_gt4,trusted_major_or_critical_flaw_present |
| ZHr0JajZfH | reject | accept | accept | reject | 4 | 2 | 2 | 7 | 0 | positive | positive | positive | independent_lt3,unresolved_gt4 |
