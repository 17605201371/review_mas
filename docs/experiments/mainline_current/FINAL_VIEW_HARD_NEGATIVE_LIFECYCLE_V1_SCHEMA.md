# Final-View Hard-Negative / Unresolved Lifecycle Schema v1

本脚本只做离线派生视图，不改 runtime、不改 live `ReviewState`。

## 派生字段

- `active_unresolved_count`：仍可能代表论文风险的 open unresolved。
- `resolved_by_support_unresolved_count`：相关 claim 已有 real support，但 unresolved 仍未关闭。
- `meta_or_system_unresolved_count`：包含 fallback、JSON、excerpt、system limitation 等系统侧信息。
- `open_review_question_count`：没有绑定明确 paper defect 的普通待查问题。
- `stale_evidence_gap_count`：claim 已有 support，但仍保留 `lacks grounded evidence` gap。
- `trusted_hard_negative_count`：非 fallback/meta，且 grounded/confirmed/confidence 足够的 major/critical flaw。
- `candidate_only_hard_negative_count`：仍只是 candidate 的 major/critical flaw，不应直接等同 confirmed weakness。
- `fallback_or_meta_flaw_count`：fallback、malformed JSON 或 system-meta flaw。

## 原则

这些字段用于 final decision/report 前的 derived view。它们不能写回 live state，也不能改变 manager/recovery 轨迹。
