# Paper Figure and Table Plan v1

## 目标

本文件规划论文中应使用的主图、主表和 case study。当前目标不是继续扩实验，而是把已有结果组织成可写论文的形式。

## Table 1：Mainline-Final-v1 主结果表

### 内容

- runtime health
- support state
- criterion simulation
- negative anchor confirmation
- support quality filter
- final recommendation view

### 来源

- `PAPER_MAIN_RESULTS_TABLE_V1.md`
- `MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md`

### 论文作用

展示系统从二分类 collapse 转向 final-view diagnostic recommendation。

## Table 2：Support Provenance Reconciliation

### 内容

- raw fallback strong
- decision real strong
- recommendation-eligible support
- accept_like rows with fallback strong

### 来源

- `MAINLINE_FINAL_V1_METRIC_CONSISTENCY_AUDIT.md`
- `SUPPORT_PROVENANCE_RECONCILIATION_V1.md`

### 论文作用

解释为什么 raw state 还有 fallback strong，但 final-view 结论仍然可信。

## Table 3：Support Quality Filter Trade-off

### 内容

- sim4 current combined
- nonabstract independent
- two positive criteria
- empirical/method-result
- high precision

### 来源

- `FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_SIMULATION.md`

### 论文作用

证明 support quality filter 不是最终二分类规则，而是 precision-recall trade-off 诊断。

## Table 4：Final Recommendation View Distribution

### 内容

- accept_like
- borderline_positive
- borderline_insufficient
- reject_like
- not_assessable
- gold x recommendation distribution

### 来源

- `FINAL_RECOMMENDATION_VIEW_V1_SIMULATION.md`
- `FINAL_RECOMMENDATION_REPORT_V1_AUDIT.md`

### 论文作用

说明多类 recommendation view 的必要性。

## Figure 1：System Pipeline

### 内容

```text
Paper -> Multi-turn ReviewState -> Evidence Binding / JSON Robustness
      -> Criterion Grounding / Support Quality
      -> Final Recommendation View
```

### 论文作用

展示系统不是黑箱 final reviewer，而是 stateful evidence-grounded pipeline。

## Figure 2：Decision Collapse vs Recommendation View

### 内容

左侧：runtime `39/39 reject`。

右侧：final-view 分布：

- accept_like = 1
- borderline_positive = 12
- borderline_insufficient = 3
- reject_like = 1
- not_assessable = 22

### 论文作用

直观展示为什么硬二分类不是合适输出。

## Figure 3：Support Provenance Separation

### 内容

```text
raw fallback support -> diagnostic only
real-claim support -> decision-eligible
support quality -> recommendation filter
```

### 论文作用

解释 fallback contamination 与 final-view 隔离。

## Case Study 1：High-precision accept-like

### 样本

- `KI9NqjLVDT`

### 来源

- `PAPER_CASE_STUDIES_V1.md`

## Case Study 2：Borderline positive false-accept risk

### 样本

- `WNxlJJIEVj`

### 来源

- `PAPER_CASE_STUDIES_V1.md`

## Case Study 3：Not-assessable gold accept

### 样本

- `QAAsnSRwgu`

### 来源

- `PAPER_CASE_STUDIES_V1.md`

## 当前不建议放进主表的内容

1. sticky / throttle 细节表：可放 discussion 或 appendix。
2. 每轮 p24/p25 中间试错数字：只保留为 negative findings。
3. final accept/reject accuracy 单表：容易误导论文主线。
