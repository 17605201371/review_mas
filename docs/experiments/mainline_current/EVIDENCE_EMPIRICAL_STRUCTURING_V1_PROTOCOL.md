# Evidence Empirical Structuring v1 Protocol

## 目标

本轮只修 Evidence Agent 对 empirical/result/table evidence 的结构化与强度判定，不改 final decision、recovery、fallback、state hygiene 或 criterion aggregation。

## 背景

`Evidence Empirical Observability v1 mixed16 4B` 显示：

- `evidence_turns = 83`
- `field_turns = 67`
- `empirical_payload_without_strong_support = 20`
- `strong_empirical_payload_formed = 7`
- `payload_empirical_evidence_total = 33`
- `payload_strong_empirical_total = 8`

这说明系统经常已经看到或结构化了 empirical evidence，但没有稳定形成 strong empirical support。当前不应调 final recommendation，也不应回到 sticky/throttle；下一刀应先修 Evidence Agent 的 empirical structuring/strength policy。

## 改动范围

仅修改 `agent_system/review_prompts.py` 的 Evidence Agent 输出约束：

- 明确 result/experiment/table/figure/ablation/baseline-comparison evidence 直接支持 allowed claim 时应使用 `strength="strong"`。
- method/mechanism evidence 只有解释核心 claim 如何实现时才可 strong，否则 medium。
- abstract/title/conclusion-only positive evidence 仍不得默认 strong。
- 若上下文包含 relevant empirical numbers/results/tables/figures/ablations/datasets/metrics/baselines，应优先输出一个 empirical item。
- 对 empirical evidence 要使用 `support_source_bucket="result_or_experiment"`。

## 不改内容

- 不改 final decision。
- 不改 evidence parser / fallback / binding guard。
- 不改 recovery phase。
- 不改 state hygiene。
- 不改 criterion-aware report。

## 评估口径

继续用固定 `support_quality_v1_mixed16.parquet` 16 条 4B 诊断集，对比 v1 observability 与 empirical structuring v1：

- `strong_empirical_payload_formed`
- `payload_strong_empirical_total`
- `rows_with_strong_empirical`
- `raw_empirical_no_payload_evidence`
- `empirical_payload_without_strong_support`
- final decision 只作为 health check，不作为主目标。
