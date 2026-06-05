# Criterion-Aware Final Report Section v1 运行对比

## 运行范围

- 数据集：`outputs/results_main/review_infer/criterion_aware_final_report_v1_mixed16.jsonl`
- 样本数：16
- 模型：4B
- 模式：S4，`max_turns=8`
- 结果副本：`/reviewF/datasets/criterion_aware_final_report_v1_mixed16.jsonl`

## 结构检查

| 指标 | 数值 |
|---|---:|
| 输出行数 | 16 |
| 包含 `4. Criterion Assessment` 的报告数 | 16 |
| criterion section 覆盖率 | 100% |
| 运行是否完成 | 是 |

## 决策健康检查

| 指标 | 数值 |
|---|---:|
| predicted accept | 0 |
| predicted reject | 16 |
| predicted undecided | 0 |

这说明本轮 report-only 改动没有解决 always-reject 问题。该结果符合预期，因为本轮没有修改 final decision、evidence binding、state hygiene 或 flaw lifecycle。

## Criterion 覆盖与 grounding

基于 `scripts/analyze_criterion_dimensions.py` 的报告层审计：

| 维度 | covered | grounded |
|---|---:|---:|
| novelty / originality | 16 | 16 |
| significance / contribution | 16 | 16 |
| technical soundness | 16 | 12 |
| empirical adequacy | 16 | 12 |
| clarity / reproducibility | 16 | 16 |

报告层检查显示：新增 section 能稳定覆盖五个审稿维度，且没有出现 unsupported critique 或 meta-leakage。

## State / evidence 反查口径

基于 `scripts/analyze_support_quality_and_criteria.py` 的 state/evidence 反查：

| 指标 | 数值 |
|---|---:|
| real_strong_support_total | 6 |
| non_abstract_support_total | 6 |
| empirical_support_total | 4 |
| method_support_total | 2 |
| table_or_figure_support_total | 1 |
| independent_support_group_total | 6 |
| fallback_or_unbound_strong_support | 0 |
| unresolved_count | 89 |
| major_or_critical_flaws | 18 |

这个口径更保守，也更接近论文核心问题：final report 能覆盖维度，但底层 evidence/support 仍不足，且 unresolved/flaw 负担仍然很重。

## 离线 simulation 结果

| Simulation | Accuracy | Macro-F1 | Accept Recall | Reject Recall | Pred Accept | False Accept | Recovered Accept |
|---|---:|---:|---:|---:|---:|---:|---|
| original | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 0 | - |
| abstract-only excluded | 0.5625 | 0.4589 | 0.1250 | 1.0000 | 1 | 0 | `giU9fYGTND` |
| non-abstract support >= 1 | 0.5625 | 0.4589 | 0.1250 | 1.0000 | 1 | 0 | `giU9fYGTND` |
| independent groups >= 2 | 0.5625 | 0.4589 | 0.1250 | 1.0000 | 1 | 0 | `giU9fYGTND` |
| empirical support for empirical claims | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 0 | - |
| method + result combination | 0.5000 | 0.3333 | 0.0000 | 1.0000 | 0 | 0 | - |
| criterion-grounded accept signal | 0.5000 | 0.4667 | 0.2500 | 0.7500 | 4 | 2 | `IdAyXxBud7`, `giU9fYGTND` |

criterion-grounded accept signal 会误翻 `GSckuQMzBG` 和 `77plFC53J5`，所以 criterion 维度现在不能进入 final decision。

## 结论

本轮运行证明：

1. `Criterion Assessment` 章节可稳定生成，适合保留为报告层结构补齐。
2. 该改动没有改善 accept collapse，也不应该被解释为 decision 改进。
3. 如果把 criterion grounding 当作 accept-like signal，会产生 false accept，因此不能接入 final decision。
4. 下一步的 runtime 主线仍应优先处理 evidence/support formation、final-view hygiene、candidate/unresolved lifecycle，而不是 criterion-based decision rule。
