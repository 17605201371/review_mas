# Final-View Negative Blocker View v1 Results

## 结论

这轮派生视图确认：当前 9B fulltest39 中几乎没有可直接用于 final decision 的 `strong_reject_blocker`。false accept 主要落在 `positive_support_without_negative_blocker` 或 `weak_negative_candidate`，说明系统已经能形成正向 evidence，但还不能可靠形成 paper-grounded negative blocker。

## Label distribution

| label | count |
| --- | --- |
| meta_limitation_only | 4 |
| no_clear_signal | 5 |
| not_assessable_burden | 5 |
| strong_reject_blocker | 2 |
| weak_negative_candidate | 23 |


## Decision-use distribution

| decision_use | count |
| --- | --- |
| can_block_accept_like | 2 |
| human_review_or_report_warning_only | 23 |
| reject_like_or_not_assessable_health_check | 5 |
| report_limitation_only | 4 |
| route_to_not_assessable_not_reject | 5 |


## False accept vs recovered accept

| group | label | count |
| --- | --- | --- |
| false_accept | not_assessable_burden | 1 |
| false_accept | weak_negative_candidate | 6 |
| recovered_accept | weak_negative_candidate | 3 |


## 解释

- 如果直接把 `positive_support_without_negative_blocker` 当 accept，会产生 false accept。
- 如果直接把 `not_assessable_burden` 当 reject，会误伤 recovered accept。
- 当前缺的是 criterion-linked negative blocker 的形成与验证，不是更多 support 阈值。
