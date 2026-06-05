# Final-View Flaw Lifecycle / Meta-Leakage Simulation v1

## 结论

这轮离线模拟说明：**flaw lifecycle / meta-leakage 是当前 final-view decision 的关键缺口，但仅靠简单的 meta/unresolved 过滤还不能安全解决 false accept。**

在 9B fulltest39 上，Sim4 criterion aggregation 的 false accept 样本多数没有显式 negative evidence，也没有 confirmed grounded flaw；它们的问题更多表现为 unresolved/gap/fallback/meta 对象缺少生命周期分类。可是这些 unresolved/meta 特征同样出现在 recovered accept 中，所以简单规则会同时挡掉 true accept。

因此，下一步不能直接把这些 lifecycle filter 接入 decision。更合理的下一刀是：**建立 criterion-linked negative blocker / flaw grounding view**，把“真实 paper weakness”与“系统上下文不足 / 待验证问题 / fallback 产物”明确分开。

## Aggregate

| group | metric | value |
| --- | --- | --- |
| false_accept_lifecycle_totals | meta_unresolved_count | 11 |
| false_accept_lifecycle_totals | hard_paper_unresolved_count | 1 |
| false_accept_lifecycle_totals | hard_meta_unresolved_count | 2 |
| false_accept_lifecycle_totals | generic_unresolved_count | 25 |
| false_accept_lifecycle_totals | fallback_or_meta_flaw_count | 1 |
| false_accept_lifecycle_totals | meta_flaw_count | 1 |
| false_accept_lifecycle_totals | stale_or_missing_gap_count | 15 |
| false_accept_lifecycle_totals | confirmed_grounded_paper_flaw_count | 0 |
| false_accept_lifecycle_totals | candidate_grounded_paper_flaw_count | 0 |
| recovered_accept_lifecycle_totals | meta_unresolved_count | 7 |
| recovered_accept_lifecycle_totals | hard_paper_unresolved_count | 1 |
| recovered_accept_lifecycle_totals | hard_meta_unresolved_count | 2 |
| recovered_accept_lifecycle_totals | generic_unresolved_count | 10 |
| recovered_accept_lifecycle_totals | fallback_or_meta_flaw_count | 0 |
| recovered_accept_lifecycle_totals | meta_flaw_count | 0 |
| recovered_accept_lifecycle_totals | stale_or_missing_gap_count | 9 |
| recovered_accept_lifecycle_totals | confirmed_grounded_paper_flaw_count | 0 |
| recovered_accept_lifecycle_totals | candidate_grounded_paper_flaw_count | 0 |


## Demotion Variant Results

| variant | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids | demoted_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim4_original | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |  |
| demote_hard_paper_unresolved_ge1 | 0.6667 | 0.5111 | 0.2222 | 0.8 | 8 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31 | KI9NqjLVDT, aTBE70xiFw |
| demote_fallback_or_meta_flaw_ge1 | 0.6923 | 0.5667 | 0.3333 | 0.8 | 9 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT | a6SntIisgg |
| demote_stale_or_missing_gap_ge3 | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, kam84eEmub | BXY6fe7q31 | 1HCN4pjTb4, KI9NqjLVDT, NnExMNiTHw, aTBE70xiFw, ye3NrNrYOY |
| demote_meta_unresolved_ge2 | 0.7179 | 0.4923 | 0.1111 | 0.9 | 4 | WLgbjzKJkk, aTBE70xiFw, ye3NrNrYOY | 1HCN4pjTb4 | BXY6fe7q31, KI9NqjLVDT, NnExMNiTHw, WpXq5n8yLb, a6SntIisgg, kam84eEmub |
| demote_generic_unresolved_ge4 | 0.7179 | 0.4923 | 0.1111 | 0.9 | 4 | WpXq5n8yLb, aTBE70xiFw, kam84eEmub | KI9NqjLVDT | 1HCN4pjTb4, BXY6fe7q31, NnExMNiTHw, WLgbjzKJkk, a6SntIisgg, ye3NrNrYOY |
| demote_hard_or_fallback_flaw | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31 | KI9NqjLVDT, a6SntIisgg, aTBE70xiFw |
| demote_any_lifecycle_warning | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | WLgbjzKJkk |  | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT, NnExMNiTHw, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY |


## 解释

- `hard_paper_unresolved` 只能挡住少量 false accept，不能覆盖主要错误。
- `meta_unresolved` 和 `stale_gap` 在 false accept 与 recovered accept 中都很常见，不能直接作为 reject blocker。
- `fallback_or_meta_flaw` 能解释部分错误，如 fallback flaw 进入 major candidate，但覆盖率不足。
- 当前状态缺少“confirmed grounded paper weakness”的可靠标注，所以 criterion aggregation 会把“有局部正向 support 的 reject 样本”误判为 accept-like。

