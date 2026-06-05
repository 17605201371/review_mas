# MAINLINE_FINAL_V1_9B_CASE_STUDIES

这些样本用于解释论文中的关键现象：runtime decision 保守、final-view 能恢复少量 accept、borderline_positive 不能直接映射为 accept、context limitation 应进入 not-assessable。

| paper_id | gold | runtime_pred | soft_view | hard_negative_view | real_strong | nonabstract | empirical | independent_groups | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| jVEoydFOl9 | accept | reject | None | not_assessable_context_limited | 4 | 4 | 2 | 3 | support_positive_but_review_context_limited |
| BXY6fe7q31 | accept | reject | None | not_assessable_hard_negative_unverified | 1 | 1 | 1 | 1 | negative_concern_exists_but_not_grounded |
| uOrfve3prk | reject | reject | None | not_assessable_context_limited | 2 | 2 | 1 | 2 | support_positive_but_review_context_limited |
| ye3NrNrYOY | reject | reject | None | not_assessable_context_limited | 2 | 2 | 1 | 2 | support_positive_but_review_context_limited |
| hj323oR3rw | accept | reject | None | not_assessable_targetless_unresolved | 0 | 0 | 0 | 0 | targetless_unresolved_too_high |
