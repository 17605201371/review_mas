# Final-View Unresolved / Candidate-Flaw Classifier v1 Decision

## 结论

本轮分类器支持继续推进 final-view derived recommendation，但仍不应改 live state。

- `classifier_view` 恢复 accept：`LebzzClHYw`。
- false accept：`无`。
- `review_context_limitation` 总数：`34`。
- `open_review_question` 总数：`0`。
- `candidate_hard_flaw` 总数：`11`。
- `system_or_fallback_flaw` 总数：`26`。

## 对论文主线的含义

当前系统的 reject bias 不是单纯阈值问题。大量 negative item 实际属于系统限制、上下文限制、未验证候选或普通待查问题。它们需要在 final-view 层被分区展示：Confirmed Weaknesses、Potential Concerns、Review Limitations、Unresolved Questions，而不是全部压成 Key Weaknesses。

## 下一步

下一步可以做 **Criterion-Aware Final Report Section v2 / Final-View Report Renderer v1**：把这些分类用于报告渲染，不进入 live state，不直接改变 runtime manager。推荐先改 report rendering，再考虑 final recommendation policy runtime 化。
