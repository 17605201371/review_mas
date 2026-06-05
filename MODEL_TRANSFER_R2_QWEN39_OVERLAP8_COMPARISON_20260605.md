# R2 Qwen39 Overlap8 vs DeepSeek API Comparison

## 对比口径

本报告修正了此前误用旧 Qwen smoke8 baseline 的问题。

当前 Qwen 基线使用：

- `/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524 2/full39_20260602_head60ce62a_qwen35_t7.jsonl`

从该 full39 中按 DeepSeek 8 条样本 ID 精确截取：

```text
WNxlJJIEVj
WLgbjzKJkk
9zEBK3E9bX
ZHr0JajZfH
X41c4uB4k0
QAAsnSRwgu
hj323oR3rw
kam84eEmub
```

DeepSeek 对比文件：

- `r2_baseline_deepseek_v3.jsonl`
- `local_deepseek_v3_full8.jsonl`

其中 `r2_baseline_deepseek_v3.jsonl` 是当前更严格的 r2 baseline 对比对象；`local_deepseek_v3_full8.jsonl` 是同 ID 的另一轮 DeepSeek full8 输出，用于辅助判断上限，但不应和 r2 baseline 混写成同一结论。

## 核心指标

| metric | Qwen r2 overlap8 | DeepSeek r2 baseline8 | DeepSeek local full8 |
|---|---:|---:|---:|
| avg_reward | 0.3515 | 0.4158 | 0.5060 |
| predicted_accept | 0 | 1 | 0 |
| real_strong_support_total | 8 | 18 | 23 |
| independent_support_group_total | 7 | 16 | 19 |
| claims_with_2plus_independent_support | 3 | 2 | 5 |
| papers_with_real_strong_support | 4 | 8 | 7 |
| zero_real_papers | 4 | 0 | 1 |
| empirical_real_strong_support_count | 2 | 10 | 19 |
| method_real_strong_support_count | 6 | 8 | 4 |
| table_or_figure_real_strong_support_count | 1 | 8 | 10 |
| result_or_experiment_real_strong_support_count | 1 | 2 | 7 |
| verified_moderate_support_total | 3 | 25 | 24 |
| diagnostic_support_signal_total | 11 | 43 | 47 |
| final_support_total | 8 | 18 | 23 |
| final_support_direct_strong_count | 2 | 6 | 16 |
| final_support_promoted_from_medium_count | 6 | 12 | 7 |
| support_trace_total | 18 | 54 | 68 |
| support_trace_included_count | 8 | 18 | 23 |
| support_trace_dropped_count | 10 | 36 | 45 |
| support_trace_hygiene_filtered_count | 2 | 20 | 22 |
| support_trace_semantic_mismatch_count | 1 | 8 | 9 |
| negative_evidence_candidate_count | 1 | 3 | 2 |
| verified_negative_flaw_count | 1 | 2 | 4 |
| verified_actionable_negative_flaw_count | 0 | 0 | 0 |
| grounded_weakness_count | 0 | 0 | 0 |
| assessment_limitation_flaw_count | 3 | 3 | 5 |
| state_contamination_count | 6 | 3 | 7 |
| evidence_gap_open_count | 27 | 3 | 2 |
| evidence_gap_resolved_count | 7 | 28 | 28 |
| unresolved_open_count | 6 | 1 | 0 |
| unresolved_open_raw_count | 42 | 19 | 33 |
| programmatic_specific_locator_count | 2 | 15 | 14 |
| recovery_attempted | 8 | 15 | 12 |
| recovery_patch_validated | 5 | 11 | 6 |
| recovery_committed | 3 | 4 | 4 |
| recovery_effective_repair | 3 | 1 | 1 |
| recovery_safe_resolution | 5 | 6 | 5 |
| evidence_agent_worker_turns | 37 | 45 | 44 |
| payload_evidence_item_total | 21 | 58 | 57 |
| evidence_agent_question_only_turns | 8 | 0 | 2 |

## Reward breakdown

| reward field | Qwen r2 overlap8 | DeepSeek r2 baseline8 | DeepSeek local full8 |
|---|---:|---:|---:|
| reward | 0.3515 | 0.4158 | 0.5060 |
| es_coverage | 0.1354 | 0.4479 | 0.5104 |
| es_depth | 0.1354 | 0.3698 | 0.4896 |
| es_empirical | 0.0729 | 0.2917 | 0.4688 |
| es_independent | 0.1042 | 0.0625 | 0.1875 |
| es_flaw_density | 0.0000 | 0.0000 | 0.0000 |
| penalty | 0.0460 | 0.0291 | 0.0000 |
| summary_align | 0.4528 | 0.4714 | 0.4497 |
| strength_align | 0.3967 | 0.3226 | 0.3517 |
| weakness_align | 0.3120 | 0.2464 | 0.2441 |
| suggestion_align | 0.2554 | 0.2572 | 0.2583 |
| global_align | 0.2891 | 0.2664 | 0.2729 |
| critique | 0.7843 | 0.5128 | 0.7201 |

## 判断

DeepSeek r2 baseline 相比 Qwen r2 overlap8 有明确提升，尤其在 positive evidence formation、empirical/table support、open gap resolution 和 locator 方面。

但这个提升没有达到“强模型显著解决系统瓶颈”的预期。主要原因是：

1. final decision 仍不可用，两个模型在这 8 条上的 `decision_correct` 都是 0。
2. grounded weakness 仍为 0，说明 hard-negative / flaw discovery 没有被 DeepSeek 自然解决。
3. verified actionable negative flaw 仍为 0，说明负向证据还没有进入可行动缺陷层。
4. DeepSeek 的 support 生成更强，但也带来更多 hygiene filtered / semantic mismatch，说明机制层过滤仍是瓶颈。

更准确的结论是：

> DeepSeek API 提高了证据形成能力，但没有从根本上解决 final recommendation、grounded weakness 和 hard-negative recovery。当前论文叙事仍应强调机制约束、verified support、state hygiene 和 recovery validator，而不是“大模型自然带来审稿能力跃迁”。

## 下一步

如果要证明模型能力差异，需要补一个严格同代码、同 prompt、同 ID、同配置的 Qwen r2 8/39 API 或本地运行结果。当前 `full39_20260602_head60ce62a_qwen35_t7` 可以作为 r2 Qwen full39 基线，但它是 full39 中截取的 8 条，不是独立重跑的 API same-run pair。

