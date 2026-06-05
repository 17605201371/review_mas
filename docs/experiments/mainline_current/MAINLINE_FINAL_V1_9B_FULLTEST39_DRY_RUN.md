# Mainline-Final-v1 9B Fulltest39 Dry Run

## 结论

这次 dry run 已完整跑满 39 条。原始 runtime final decision 仍然是 **39/39 reject**，说明 runtime decision collapse 仍存在；但 9B final states 中已经形成了大量 real-claim support，说明问题不再是模型完全找不到正向证据，而是 final-view decision / flaw lifecycle / negative blocker 仍未成熟。

离线 criterion-grounded aggregation 能恢复一部分 accept，但会产生大量 false accept。因此当前还不能进入正式 9B 主试验，也不能把 criterion aggregation 接入 runtime decision。

下一刀应转向：**Final-View Flaw Lifecycle / Meta-Leakage Simulation v1**。原因是 false accept 样本也拥有 strong support 与正向 criterion，当前系统缺少可信的 grounded negative blocker 来区分“有局部支持但仍应 reject”的论文。

## 运行配置

- model: Qwen3.5-9B
- dataset: `/reviewF/datasets/drmas_review/test.parquet`
- rows: 39
- mode: S4
- max_turns: 8
- max_model_len: 3072
- max_tokens: 640
- output: `outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl`

## 原始结果

| metric | value |
| --- | --- |
| rows | 39 |
| gold accept | 9 |
| gold reject | 30 |
| runtime accept | 0 |
| runtime reject | 39 |
| avg_reward | 0.4674 |


## Support / Hygiene 摘要

| metric | value |
| --- | --- |
| real_strong_support_total | 37 |
| non_abstract_support_total | 18 |
| empirical_support_total | 5 |
| fallback_strong_support_total | 13 |
| negative_evidence_total | 2 |
| rows_with_2plus_real_strong | 14 |
| rows_with_2plus_nonabstract | 5 |
| rows_with_empirical_support | 4 |
| unsupported_with_strong_support_count | 5 |
| stale_gap_count | 38 |
| meta_leakage_count | 14 |
| grounded_major_flaw_count | 1 |
| confirmed_critical_flaw_count | 0 |


## Criterion Decision Simulation

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept(strict) | borderline | false_accept_count | recovered_accept_count | pred_accept(lenient) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim0_current_rule | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 | 0 | 0 | - |
| sim1_support_count_rule | 0.6923 | 0.6201 | 0.5556 | 0.7333 | 13 | 0 | 8 | 5 | - |
| sim2_criterion_gated_reject | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 16 | 0 | 0 | - |
| sim3_support_quality_accept | 0.6667 | 0.5764 | 0.4444 | 0.7333 | 12 | 4 | 8 | 4 | - |
| sim4_combined_criterion_support_hygiene | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 6 | 7 | 3 | 16 |


## Safety Variant 诊断

| variant | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | borderline | false_accept_ids | recovered_accept_ids |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sim4_strict_original | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 6 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |
| safety_negative_evidence_demote | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 6 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, aTBE70xiFw, kam84eEmub, ye3NrNrYOY | 1HCN4pjTb4, BXY6fe7q31, KI9NqjLVDT |
| safety_require_nonabstract2 | 0.7179 | 0.4923 | 0.1111 | 0.9 | 4 | 12 | WpXq5n8yLb, a6SntIisgg, ye3NrNrYOY | KI9NqjLVDT |
| safety_require_empirical_support | 0.6923 | 0.4091 | 0.0 | 0.9 | 3 | 13 | NnExMNiTHw, WLgbjzKJkk, WpXq5n8yLb |  |
| safety_require_no_stale_gap_over2 | 0.6923 | 0.4777 | 0.1111 | 0.8667 | 5 | 11 | WLgbjzKJkk, WpXq5n8yLb, a6SntIisgg, kam84eEmub | BXY6fe7q31 |
| safety_nonabstract2_and_stale2 | 0.7179 | 0.4179 | 0.0 | 0.9333 | 2 | 14 | WpXq5n8yLb, a6SntIisgg |  |


## 关键解释

- 9B runtime 仍然全 reject，所以 final decision 层不能作为当前主指标。
- Sim 4 strict 恢复 3 个 accept，但 false accept 有 7 个；lenient 恢复 5 个 accept，但 false accept 增至 11 个。
- 简单 safety gate 不够：`negative_evidence_total` 对 false accept 基本无效，因为多数 false accept 没有显式 negative evidence。
- 要压住 false accept，必须引入更可靠的 flaw lifecycle / meta-leakage / grounded weakness 视图，而不是继续提高 support 阈值或直接调 accept/reject 阈值。
