# Paper Claims and Evidence Map v1

## 目的

本文件把当前主线结果转成论文可写的“主张-证据”映射，避免后续写作时把工程过程写成流水账。

## 论文核心主张 1：硬二分类 final decision 不是当前系统最可信输出

### 主张

在多轮审稿辅助中，直接输出 `accept/reject` 容易发生 decision collapse；更可靠的输出应是 evidence-grounded 的 final-view recommendation。

### 证据

- `runtime_reject = 39 / 39`
- `runtime_accept = 0`
- `avg_reward = 0.4674`

### 支撑文件

- `MAINLINE_FINAL_V1_UNIFIED_RESULTS_TABLE.md`
- `PAPER_MAIN_RESULTS_TABLE_V1.md`

### 写法建议

不要把这写成“系统分类失败”。应写成：runtime final decision 是 health check，它暴露了传统二分类层的 collapse；论文主输出转向可诊断推荐视图。

## 论文核心主张 2：Final Recommendation View 比硬映射更符合审稿辅助任务

### 主张

多类推荐视图能区分 `accept_like`、`borderline_positive`、`borderline_insufficient`、`reject_like`、`not_assessable`，比硬二分类更能表达系统证据状态。

### 证据

- `accept_like = 1`
- `borderline_positive = 12`
- `borderline_insufficient = 3`
- `reject_like = 1`
- `not_assessable = 22`

### 关键解释

- `accept_like` 是高精度正向推荐，但召回低。
- `borderline_positive` 同时包含 gold accept 和 gold reject，不能直接映射为 accept。
- `not_assessable` 表明系统缺少足够 grounded evidence，不应默认 reject。

### 支撑文件

- `FINAL_RECOMMENDATION_VIEW_V1_SIMULATION.md`
- `FINAL_RECOMMENDATION_REPORT_V1_AUDIT.md`
- `PAPER_CASE_STUDIES_V1.md`

## 论文核心主张 3：Evidence Binding 修复的是“可用支持证据”而不是 raw state 完全无污染

### 主张

系统已经能在 final-view/recommendation 层隔离 fallback-bound strong support，但 raw ReviewState 中仍保留 fallback 残留，应作为诊断指标而不是 decision evidence。

### 证据

- `raw_fallback_strong_support_excluded = 13`
- `rows_with_raw_fallback_strong = 7`
- `accept_like_rows_with_raw_fallback_strong = 0`
- fallback strong 来源均为 `abstract`

### 关键解释

论文中不能写“fallback strong 已完全消失”。正确写法是：raw fallback-bound support 被保留为污染诊断信号，但不进入 decision-eligible real-claim support 或 final-view recommendation。

### 支撑文件

- `MAINLINE_FINAL_V1_METRIC_CONSISTENCY_AUDIT.md`
- `SUPPORT_PROVENANCE_RECONCILIATION_V1.md`

## 论文核心主张 4：负向 blocker formation 目前不是可靠主线

### 主张

即使能从正文中抽到 table/result/baseline/ablation anchor，当前 4B anchor-only confirmation 仍不能稳定确认 false accept 的 reliable negative blocker。

### 证据

- anchor extraction: `10 / 10` rows 有 anchor
- quant anchor: `10 / 10`
- false accept trusted blocker: `0 / 7`
- recovered accept trusted blocker: `1 / 3`
- parse error: `0`

### 解释

问题不是 JSON 解析或锚点完全不可见，而是当前模型和可见上下文不足以稳定确认可作为 reject blocker 的负向证据。因此不能把 negative blocker 接入 final decision。

### 支撑文件

- `NEGATIVE_EVIDENCE_ANCHOR_EXTRACTION_V1.md`
- `NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_COMPARE.md`
- `PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md`

## 论文核心主张 5：Support quality filter 能提高精度，但不能替代推荐视图

### 主张

更严格的 support quality filter 可以压低 false accept，但会显著牺牲 accept recall，因此更适合作为 final-view 诊断指标，而不是硬规则。

### 证据

- `sqf_high_precision`: `false_accept = 0`, `true_accept = 1`
- `sqf_two_positive_criteria`: `false_accept = 2`, `true_accept = 2`
- `sim4_current_combined`: `false_accept = 7`, `true_accept = 3`

### 支撑文件

- `FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_SIMULATION.md`
- `PAPER_MAIN_RESULTS_TABLE_V1.md`

## 当前不可声称的内容

1. 不能声称系统已经解决 accept/reject 分类。
2. 不能声称 raw ReviewState 已完全无 fallback 污染。
3. 不能声称 negative blocker 已可用于 reject。
4. 不能声称 criterion score 可以直接决定 accept/reject。
5. 不能声称 9B 正式主实验已经完成。

## 当前可以声称的内容

1. 系统可以把 runtime decision collapse 诊断出来。
2. 系统可以把 raw fallback support 与 decision-eligible support 分开。
3. 系统可以输出更诚实的多类 final-view recommendation。
4. 系统可以通过 support quality / criterion grounding 解释为什么某些样本只能 borderline 或 not-assessable。
5. 负结果表明后置 controller 和强造 blocker 不是当前最有效方向。
