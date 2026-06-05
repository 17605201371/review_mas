# Soft Evidence Recommendation v1 Schema

本层是离线 recommendation simulation，不改 runtime。目标是减少单条硬约束对 final recommendation 的支配。

核心字段：

- `support_score`: real / non-abstract / empirical / independent support 与 positive grounded criterion 的软分。
- `negative_score`: grounded hard-negative、negative grounded criterion、ungrounded negative unresolved 的软分。
- `uncertainty_score`: context limitation、targetless unresolved、not-assessable criterion、meta leakage 的不确定性分。
- `net_support`: support_score 减去 negative 与 uncertainty 折扣后的净正向信号。
- `reject_pressure`: negative 与 uncertainty 对 reject-like 的压力。

原则：模型或 report 负责产生 criterion / evidence 信号；规则只负责 provenance 约束和软聚合，不把 novelty / soundness 裸规则化。
