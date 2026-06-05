# Mainline-Final-v1 9B Context v2.2 Unified Readiness Report 2026-05-03

## 总结论

最新 9B fulltest39 已达到“主试验 dry-run 可用、正式主结果还需按 final-view 口径解释”的阶段。runtime 决策仍然 39/39 reject，但 evidence/support/report 层已经比早期版本稳定得多。

## Runtime / Preflight

- preflight status: `pass`
- row_count: `39`
- gold: accept `9`, reject `30`, unknown `0`
- legacy_controller_active_turns: `0`
- evidence_json_invalid_or_missing_count: `0`
- evidence_json_fallback_payload_turns: `0`

## Decision Health

| metric | value |
|---|---:|
| `accuracy` | 0.7692 |
| `macro_f1` | 0.4348 |
| `accept_recall` | 0.0 |
| `reject_recall` | 1.0 |
| `predicted_accept_count` | 0 |
| `false_accept_count` | 0 |
| `false_reject_count` | 9 |

解释：二分类仍 collapse 成 reject，因此只能作为 health check；不应作为论文唯一主指标。

## Evidence / Support Quality

| metric | value |
|---|---:|
| `real_strong_support_total` | 49 |
| `nonabstract_strong_support_total` | 49 |
| `empirical_strong_support_total` | 38 |
| `method_strong_support_total` | 11 |
| `table_or_figure_strong_support_total` | 1 |
| `ablation_strong_support_total` | 35 |
| `fallback_strong_support_total` | 0 |
| `unbound_strong_support_total` | 0 |
| `rows_with_2plus_real_strong_support` | 17 |
| `accept_rows_with_empirical_support` | 5 |

解释：positive support formation 已经明显可用，且没有 fallback strong 污染；但 accept 样本仍未被 runtime decision 利用。

## State / Recovery

| metric | value |
|---|---:|
| `unresolved_count` | 269 |
| `evidence_gap_count` | 110 |
| `flaw_count` | 48 |
| `conflict_note_count` | 73 |
| `patch_emitted_count` | 96 |
| `patch_validated_count` | 90 |
| `patch_committed_count` | 1 |
| `rows_with_any_commit` | 1 |

解释：recovery 框架仍能运行，但有效 commit 很少；当前不应继续调 controller，应把 recovery 作为辅助指标。

## Recommendation View v2

| metric | value |
|---|---:|
| `borderline_insufficient` | 2 |
| `borderline_positive` | 15 |
| `not_assessable` | 21 |
| `reject_like` | 1 |

解释：`borderline_positive=15` 说明正向 support 形成了，但系统仍不应直接升级为 accept-like；`not_assessable=21` 说明大量样本需要暴露审稿不确定性，而不是强行二分类。

## Final-View Flaw Lifecycle

| metric | value |
|---|---:|
| `derived_strict_predicted_accept_count` | 16 |
| `derived_strict_false_accept_count` | 14 |
| `derived_strict_recovered_accept_count` | 2 |
| `flaw_fallback_or_malformed_artifact` | 25 |
| `flaw_excerpt_limitation` | 14 |
| `unresolved_ungrounded_unresolved` | 218 |

解释：简单 derived strict 太宽，会产生 14 个 false accept，因此不能作为 policy；必须保留 v2 的 borderline/not_assessable 分层。

## Final-View Report Renderer v2

| metric | value |
|---|---:|
| `reports` | 39 |
| `confirmed_weaknesses` | 2 |
| `potential_concerns` | 4 |
| `review_limitations` | 103 |
| `unresolved_questions` | 228 |
| `reports_with_review_limitations` | 37 |
| `confirmed_weakness_meta_leak_rows` | 0 |

解释：这是本轮最重要的论文层进展。meta/fallback/excerpt limitation 没有进入 Confirmed Weakness，报告层可以更诚实地区分论文缺陷和系统限制。

## Go / No-Go

- Go: 可以作为 9B mainline dry-run / paper pack 的核心结果。
- No-Go: 不能声称 runtime accept/reject 已解决，不能把 derived strict accept-like 当 final policy。
- Next: 冻结这个 spec，进入论文主表整理和必要复现实验；不再新增 controller 分支。
