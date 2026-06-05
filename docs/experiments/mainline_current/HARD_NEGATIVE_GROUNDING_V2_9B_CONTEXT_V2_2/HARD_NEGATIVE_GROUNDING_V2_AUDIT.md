# Hard-Negative Grounding v2 Audit

| metric | value |
| --- | --- |
| gold_reject | 30 |
| old_view_borderline_positive | 15 |
| v4_not_assessable_context_limited | 15 |
| grounded_hard_negative_v2_total | 9 |
| context_limitation_total | 97 |
| ungrounded_negative_total | 13 |
| targetless_open_question_total | 198 |
| old_view_not_assessable | 21 |
| v4_reject_like | 6 |
| gold_accept | 9 |
| v4_not_assessable_targetless_unresolved | 14 |
| old_view_reject_like | 1 |
| v4_not_assessable_hard_negative_unverified | 4 |
| old_view_borderline_insufficient | 2 |

## View transitions

| transition | count |
| --- | --- |
| borderline_insufficient -> not_assessable_targetless_unresolved | 2 |
| borderline_positive -> not_assessable_context_limited | 15 |
| not_assessable -> not_assessable_hard_negative_unverified | 4 |
| not_assessable -> not_assessable_targetless_unresolved | 12 |
| not_assessable -> reject_like | 5 |
| reject_like -> reject_like | 1 |
