# Criterion-Grounded Decision Schema v1

本文件定义离线 final decision simulation 的派生字段和规则。

## 设计原则

本轮不改 runtime、不改 `ReviewState`、不重跑模型，也不让模型自由输出 accept/reject。模型或已有报告只提供审稿维度信号；规则层只做证据约束、状态卫生约束和决策校准。

## Criterion 字段

- `criterion_rating_novelty / significance / soundness / empirical / clarity`: 规则从 final report 中派生的维度倾向，取值包括 `moderate_or_strong`、`weak`、`neutral_or_mentioned`、`not_assessable`、`missing`。
- `criterion_grounded_*`: 维度判断是否有 evidence section、claim/evidence/table/figure 引用，或明确标记为 not assessable。
- `criterion_not_assessable_*`: 系统是否承认该维度上下文不足。

## Support 字段

- `real_strong_support_total`: 绑定到真实 claim 的 strong positive support 总数。
- `non_abstract_support_total`: 非 abstract 的 strong support 数量。
- `empirical_support_total`: result / table / figure / ablation support 数量。
- `independent_support_group_total`: 去重后的独立 support group 数量。

## Flaw / Hygiene 字段

- `confirmed_critical_flaw_count`: grounded confirmed critical flaw。
- `grounded_major_flaw_count`: grounded major/critical flaw。
- `ungrounded_candidate_flaw_count`: 未 grounding 的 candidate flaw。
- `stale_gap_count`: 有 strong support 时仍存在的可能 stale gap。
- `meta_leakage_count`: excerpt/system/fallback/recovery 相关 meta 信息进入负面状态。

## 模拟规则

- Sim 0: 当前 final decision。
- Sim 1: strong support count rule。
- Sim 2: criterion-gated reject。
- Sim 3: support-quality accept。
- Sim 4: combined criterion + support quality + hygiene。

本轮输出只用于离线诊断，不直接作为论文系统 runtime decision。
