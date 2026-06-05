# Evidence Lineage Support View v1 Schema

本层是离线 final-view，不改 live ReviewState、不重跑模型。它从 `turn_logs[*].worker_payloads[*].payload.evidence_map` 收集 Evidence Agent 曾经产生过的 evidence，过滤真实 claim 上的 strong support，并按 `(claim_id, evidence text, source, section)` 去重。

核心字段：`lineage_real_strong`、`lineage_nonabstract`、`lineage_empirical`、`lineage_method`、`lineage_independent_groups`、`lineage_nonabstract_independent_groups`。

该 view 的目的不是直接改 accept/reject，而是衡量 final state 压缩前已经出现过多少可用正向证据。
