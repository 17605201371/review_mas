# Mainline-Final-v1 Failure Taxonomy

## Taxonomy 分布

| taxonomy | count |
| --- | --- |
| reject_like_no_valid_support | 21 |
| false_reject_no_valid_real_support | 7 |
| borderline_valid_support | 5 |
| false_accept_support_ignores_grounded_flaw | 2 |
| reject_like_grounded_critical | 2 |
| recovered_accept_valid_support | 1 |
| false_reject_insufficient_independent_support | 1 |

## Accept 样本状态

| metric | value |
| --- | --- |
| gold_accept_count | 9 |
| accept_with_valid_real_strong | 2 |
| accept_with_2plus_valid_real_strong | 1 |
| accept_with_nonabs_support | 2 |
| accept_with_empirical_support | 2 |
| accept_with_2plus_independent_groups | 1 |

## Reject 样本风险

| metric | value |
| --- | --- |
| gold_reject_count | 30 |
| reject_with_accept_like_valid_support | 2 |
| reject_with_borderline_valid_support | 5 |
| reject_with_empirical_support | 6 |
| reject_with_2plus_independent_groups | 2 |

## 结论

当前主瓶颈不再是 fallback strong support，而是 valid-looking support 是否真正达到 paper-level sufficiency。下一步论文主结果应把 false accept/false reject 分解为 support depth、independence、empirical adequacy 和 grounded flaw 四类，而不是继续调 accept/reject 阈值。
