# Method / Soundness Evidence Formation Audit v1

## 结论

Soft Focus v2 已经能形成大量 real/non-abstract/empirical support，但 high-precision accept-like 只能恢复 1 条，主因不是 fallback binding，而是 method support、soundness/novelty criterion 与 hard-negative burden 没有同时满足。

## 汇总

| metric | value |
| --- | --- |
| total_rows | 39 |
| gold_accept_count | 9 |
| gold_reject_count | 30 |
| accept_like_count | 0 |
| borderline_positive_count | 5 |
| gold_accept_with_method_support | 1 |
| gold_accept_with_soundness_positive | 1 |
| gold_accept_with_novelty_positive | 1 |
| borderline_with_method_support | 3 |
| borderline_with_soundness_positive | 3 |

## Gold accept case audit

| paper_id | view | real | nonabs | empirical | method | independent | unresolved | major | novelty | soundness | empirical_rating | missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hj323oR3rw | not_assessable | 0 | 0 | 0 | 0 | 0 | 5 | 0 | not_assessable | not_assessable | not_assessable | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| QAAsnSRwgu | not_assessable | 0 | 0 | 0 | 0 | 0 | 4 | 0 | not_assessable | not_assessable | not_assessable | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| X41c4uB4k0 | borderline_insufficient | 1 | 1 | 1 | 0 | 1 | 1 | 0 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive |
| gzqrANCF4g | not_assessable | 0 | 0 | 0 | 0 | 0 | 8 | 0 | not_assessable | not_assessable | not_assessable | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| KI9NqjLVDT | not_assessable | 0 | 0 | 0 | 0 | 0 | 5 | 0 | not_assessable | not_assessable | not_assessable | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,unresolved_gt4,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| 1HCN4pjTb4 | not_assessable | 0 | 0 | 0 | 0 | 0 | 3 | 0 | not_assessable | not_assessable | not_assessable | real_strong_lt3,nonabstract_lt3,no_empirical_support,no_method_support,independent_lt3,novelty_not_positive,soundness_not_positive,empirical_not_positive |
| LebzzClHYw | borderline_positive | 2 | 2 | 1 | 1 | 2 | 1 | 0 | positive | positive | positive | real_strong_lt3,nonabstract_lt3,independent_lt3 |
| BXY6fe7q31 | borderline_positive | 3 | 3 | 3 | 0 | 3 | 10 | 0 | not_assessable | not_assessable | positive | no_method_support,unresolved_gt4,novelty_not_positive,soundness_not_positive |
| jVEoydFOl9 | reject_like | 1 | 1 | 1 | 0 | 1 | 3 | 1 | not_assessable | not_assessable | positive | real_strong_lt3,nonabstract_lt3,no_method_support,independent_lt3,trusted_major_or_critical_flaw_present,novelty_not_positive,soundness_not_positive |
