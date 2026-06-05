# Final Recommendation Policy v4 Final

## 结论

v4 解决两个问题：

1. hard-negative grounding：不再把 targetless/context-limited negative 当作 hard-negative；只有 evidence/claim/criterion grounded 的 empirical/soundness blocker 才进入 `reject_like`。
2. final recommendation policy：`borderline_positive` 不自动 accept；遇到上下文限制时降为 `not_assessable_context_limited`。

## View 分布

| view_v4 | count |
| --- | --- |
| not_assessable_context_limited | 15 |
| not_assessable_hard_negative_unverified | 4 |
| not_assessable_targetless_unresolved | 14 |
| reject_like | 6 |

## 与 v2 的变化

| transition | count |
| --- | --- |
| borderline_insufficient -> not_assessable_targetless_unresolved | 2 |
| borderline_positive -> not_assessable_context_limited | 15 |
| not_assessable -> not_assessable_hard_negative_unverified | 4 |
| not_assessable -> not_assessable_targetless_unresolved | 12 |
| not_assessable -> reject_like | 5 |
| reject_like -> reject_like | 1 |

## Policy

- `reject_like`: grounded hard-negative 存在。
- `not_assessable_context_limited`: 有 support，但审稿上下文不足或 fallback/meta 限制明显。
- `not_assessable_hard_negative_unverified`: 有负面疑点，但没有 grounding。
- `not_assessable_targetless_unresolved`: targetless unresolved 太多。
- `borderline_positive`: 有 support，且没有 grounded blocker / context limitation / ungrounded negative burden。
- `borderline_insufficient`: support 或 grounding 不足。

## 下一步

如果继续优化，不应调 accept 阈值；应做小样本 `Hard-Negative Grounding v2` 人工核查，确认 `grounded_hard_negative_v2_count` 的 precision。
