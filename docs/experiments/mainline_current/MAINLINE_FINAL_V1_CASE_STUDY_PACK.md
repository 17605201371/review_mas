# Mainline-Final-v1 Case Study Pack

## 定位

本文件解释 final-view invalid-binding/support-quality 过滤后的关键样本。它不用于调 runtime，也不作为 final decision 规则。

## 重点样本

| paper_id | gold | current | view_label | taxonomy | valid_real_strong | nonabs | empirical | ind_groups | grounded_major | unresolved | gaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hj323oR3rw | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 1 | 5 | 3 |
| QAAsnSRwgu | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 0 | 2 | 4 |
| X41c4uB4k0 | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 1 | 5 | 3 |
| gzqrANCF4g | accept | reject | accept_like_valid_support | recovered_accept_valid_support | 2 | 2 | 2 | 2 | 1 | 6 | 4 |
| cklg91aPGk | reject | accept | accept_like_valid_support | false_accept_support_ignores_grounded_flaw | 3 | 3 | 3 | 2 | 1 | 3 | 2 |
| fGXyvmWpw6 | reject | reject | accept_like_valid_support | false_accept_support_ignores_grounded_flaw | 2 | 2 | 2 | 2 | 1 | 4 | 4 |
| KI9NqjLVDT | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 1 | 3 | 4 |
| 1HCN4pjTb4 | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 0 | 6 | 5 |
| LebzzClHYw | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 0 | 6 | 3 |
| BXY6fe7q31 | accept | reject | reject_like_no_valid_support | false_reject_no_valid_real_support | 0 | 0 | 0 | 0 | 0 | 3 | 5 |
| jVEoydFOl9 | accept | reject | borderline_valid_support | false_reject_insufficient_independent_support | 1 | 1 | 1 | 1 | 1 | 5 | 3 |

## 读法

- `recovered_accept_valid_support` 表示当前 final-view 能恢复的 accept，但仍需要人工 case study 确认其 support 是否 paper-level sufficient。
- `false_accept_*` 表示 strong support 虽然 valid-looking，但不能自动推出 paper-level accept。
- `false_reject_*` 表示 gold accept 未恢复的主因：没有 valid real support、support 太浅、独立性不足、缺 empirical support，或负面 burden 仍过强。
