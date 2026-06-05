# Final-View Report Renderer v2 9B Fulltest39 Interpretation

## 结论

`Final-View Report Renderer v2` 可以保留为论文层 / final-view 报告渲染模块，但不应接入 runtime state mutation，也不应改变原始 accept/reject 标签。

这轮的核心进展不是提升二分类准确率，而是把 final report 中的负面内容重新分区：

- `Confirmed Weaknesses`: 只放可信、grounded 的确认缺陷。
- `Potential Concerns`: 放 candidate / provisional concern。
- `Review Limitations`: 放 fallback、malformed JSON、system/meta、excerpt limitation。
- `Unresolved Questions`: 放仍需人工核验的问题。

## 关键结果

| metric | value |
|---|---:|
| rows | 39 |
| borderline_positive | 15 |
| not_assessable | 21 |
| reject_like | 1 |
| borderline_insufficient | 2 |
| confirmed_weaknesses | 2 |
| potential_concerns | 4 |
| review_limitations | 103 |
| unresolved_questions | 228 |
| reports_with_confirmed_weakness | 2 |
| reports_with_review_limitations | 37 |
| confirmed_weakness_meta_leak_rows | 0 |

## 判断

这轮确认了一个对论文很重要的点：系统不是只能输出粗糙 reject，而是可以在 final-view 层把“论文缺陷”和“系统/上下文限制”区分开。`confirmed_weakness_meta_leak_rows = 0` 说明 meta/fallback/excerpt limitation 没有进入 Confirmed Weakness。

但 `not_assessable = 21`、`unresolved_questions = 228` 也说明：当前系统仍有大量样本不应被强行映射为 accept/reject。对论文主实验来说，runtime binary decision 应继续作为 health check；主分析应报告 support quality、criterion grounding、flaw lifecycle 和 final-view recommendation。

## 下一步

1. 冻结 `Mainline-Final-v1` spec：runtime 模块和 offline/final-view 模块必须分清。
2. 整合统一主实验表：Evidence Binding、JSON robustness、support quality、criterion grounding、flaw lifecycle、final-view report partition。
3. 不继续做 sticky/throttle/progression gate，不把 hygiene 放进 live state。
4. 若需要正式 9B 主实验，使用当前 clean runtime + final-view/offline report pack，不再临时加 controller。
