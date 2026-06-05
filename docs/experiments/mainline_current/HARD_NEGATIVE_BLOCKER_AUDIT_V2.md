# Hard-Negative Blocker Audit v2

宽松 support-quality / criterion-positive 规则的主要风险是把 gold reject 中的 result support 误当成 accept-like。high-precision 规则通过 method support、soundness/novelty positive 与 hard-negative blocker 同时约束，把这些风险样本挡回 reject。

| paper_id | runtime | support_quality | criterion_positive | high_precision | real | empirical | method | unresolved | major | novelty | soundness | empirical_rating | blockers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9zEBK3E9bX | reject | accept | accept | reject | 2 | 2 | 0 | 2 | 2 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive |
| XyB4VvF01X | reject | accept | accept | reject | 2 | 2 | 0 | 6 | 1 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive |
| GE6iywJtsV | reject | accept | accept | reject | 2 | 2 | 0 | 9 | 0 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| NnExMNiTHw | accept | accept | accept | reject | 3 | 3 | 0 | 1 | 0 | not_assessable | not_assessable | positive | no_method_support,novelty_not_positive,soundness_not_positive |
| QAgwFiIY4p | reject | accept | accept | reject | 2 | 2 | 0 | 4 | 0 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive |
| KOUAayk5Kx | reject | accept | accept | reject | 2 | 2 | 0 | 7 | 0 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| ZHr0JajZfH | reject | accept | accept | reject | 3 | 2 | 1 | 8 | 0 | positive | positive | positive | unresolved_gt4 |
