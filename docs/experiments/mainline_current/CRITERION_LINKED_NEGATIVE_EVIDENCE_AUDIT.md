# Criterion-Linked Negative Evidence Audit v1

## 结论

9B fulltest39 的 false accept 并不是因为缺少 support quality 阈值那么简单。多个 false accept 同时拥有 real strong support、non-abstract support 和 positive grounded criterion。当前缺口是：系统没有形成足够可靠的 criterion-linked negative evidence 来解释为什么这些有局部支持的论文仍应 reject。

## False Accept vs Recovered Accept totals

| group | metric | value |
| --- | --- | --- |
| false_accept | trusted_negative_blocker | 0 |
| false_accept | weak_negative_blocker | 6 |
| false_accept | negative_core_evidence_count | 0 |
| false_accept | candidate_grounded_core_flaw_count | 0 |
| false_accept | trusted_confirmed_core_flaw_count | 0 |
| false_accept | core_paper_negative_unresolved_count | 1 |
| false_accept | paper_negative_unresolved_count | 1 |
| false_accept | meta_unresolved_count | 11 |
| false_accept | generic_unresolved_count | 26 |
| false_accept | missing_support_gap_count | 15 |
| false_accept | meta_or_fallback_flaw_count | 1 |
| false_accept | ungrounded_candidate_flaw_count | 0 |
| false_accept | positive_only_flaw_grounding_count | 1 |
| false_accept | dangling_flaw_evidence_ref_count | 0 |
| false_accept | not_assessable_burden | 52 |
| recovered_accept | trusted_negative_blocker | 0 |
| recovered_accept | weak_negative_blocker | 3 |
| recovered_accept | negative_core_evidence_count | 0 |
| recovered_accept | candidate_grounded_core_flaw_count | 0 |
| recovered_accept | trusted_confirmed_core_flaw_count | 0 |
| recovered_accept | core_paper_negative_unresolved_count | 1 |
| recovered_accept | paper_negative_unresolved_count | 1 |
| recovered_accept | meta_unresolved_count | 7 |
| recovered_accept | generic_unresolved_count | 11 |
| recovered_accept | missing_support_gap_count | 9 |
| recovered_accept | meta_or_fallback_flaw_count | 0 |
| recovered_accept | ungrounded_candidate_flaw_count | 0 |
| recovered_accept | positive_only_flaw_grounding_count | 0 |
| recovered_accept | dangling_flaw_evidence_ref_count | 0 |
| recovered_accept | not_assessable_burden | 27 |


## Demotion simulations

| variant | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids | demoted_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim4_original | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |  |
| demote_trusted_negative_blocker | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |  |
| demote_trusted_or_weak_negative_blocker | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | a6SntIisgg |  | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT, NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, aTBE70xiFw, kam84eEmub, ye3NrNrYOY |
| demote_negative_core_evidence | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |  |
| demote_candidate_grounded_core_flaw | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |  |
| demote_core_paper_negative_unresolved | 0.6667 | 0.5111 | 0.2222 | 0.8 | 8 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31 | KI9NqjLVDT, aTBE70xiFw |
| demote_high_not_assessable_burden_ge6 | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | kam84eEmub |  | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT, NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, ye3NrNrYOY |
| demote_fallback_or_meta_flaw | 0.6923 | 0.5667 | 0.3333 | 0.8 | 9 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT | a6SntIisgg |


## 读法

- `trusted_negative_blocker` 覆盖率太低，说明状态中缺少可直接使用的 confirmed grounded paper weakness。
- `weak_negative_blocker` 能挡住部分 false accept，但也会影响 recovered accept，不适合直接接入 decision。
- `not_assessable_burden` 很高，但在 false accept 与 recovered accept 中都存在，说明它是系统不确定性，不是 paper-level reject 证据。
