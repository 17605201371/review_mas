# Critique Context Selection v1/v1.1 Compare

## 结论

`Critique Context Selection v1/v1.1` 暂不保留为 Mainline-Final-v1 runtime。静态 preview 证明旧 Critique 800 字前缀太浅，但 runtime 接入后没有形成足够干净的 hard-negative grounding，反而增加 targetless unresolved 与 fallback/meta flaw 负担。

## Runtime Summary

| metric | clean baseline | v1 broad negative | v1.1 safer section |
| --- | --- | --- | --- |
| real_strong_support_total | 28 | 46 | 36 |
| nonabstract_strong_support_total | 25 | 45 | 36 |
| empirical_strong_support_total | 20 | 33 | 27 |
| fallback_strong_support_total | 0 | 0 | 0 |
| unresolved_count | 190 | 238 | 215 |
| evidence_gap_count | 147 | 117 | 119 |
| flaw_count | 51 | 56 | 48 |
| conflict_note_count | 79 | 34 | 52 |
| patch_committed_count | 6 | 5 | 3 |
| rows_with_any_commit | 6 | 3 | 3 |
| avg_reward | 0.5043 | 0.4757 | 0.4779 |
| evidence_json_invalid_or_missing_count | 27 | 3 | 7 |

## Lifecycle Summary

| metric | clean baseline | v1 broad negative | v1.1 safer section |
| --- | --- | --- | --- |
| support.independent_group_total | 25 | 44 | 36 |
| support.strong_empirical_result | 11 | 17 | 14 |
| support.strong_table_or_figure | 10 | 14 | 11 |
| unresolved_gap.targetless_unresolved_count | 160 | 196 | 172 |
| unresolved_gap.stale_gap_count | 23 | 38 | 34 |
| unresolved_gap.paper_gap_count | 112 | 74 | 80 |
| unresolved_gap.meta_gap_count | 12 | 5 | 5 |
| flaw.fallback_or_meta | 35 | 46 | 42 |
| flaw.grounded_minor_or_candidate | None | 5 | 2 |
| flaw.grounded_major_or_critical | 2 | 3 | 3 |

## 解释

- v1 过宽：generic negative anchors 会把 problem motivation / task difficulty 推入 Critique 通道，导致 `targetless_unresolved` 与 `fallback_or_meta` flaw 上升。
- v1.1 收紧后更稳，但仍未达到保留标准：`targetless_unresolved_count` 仍高于 clean baseline，`rows_with_any_commit` 低于 clean baseline，`grounded_major_or_critical` 只小幅增加。
- 这说明 hard-negative 问题不能仅靠给 Critique Agent 更长上下文解决，还需要 flaw lifecycle / criterion-grounding 的离线聚合与报告层处理。
