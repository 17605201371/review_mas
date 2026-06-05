# Mainline-Final-v1 Unified Next Step Decision

## 结论

本轮统一分析支持进入主试验 dry-run 收口，但仍不建议把 runtime accept/reject 当作论文主指标。当前最可靠的成果是：evidence binding 干净、fallback flaw 被隔离、final-view classifier 保守、final report 能把确认缺陷/候选问题/审稿限制/未解决问题分区展示。

## 关键判断

- runtime predicted accept: `0`
- runtime accept recall: `0.0`
- runtime false accept: `[]`
- real strong support: `28`
- fallback strong support: `0`
- confirmed weakness meta leak rows: `0`

## 下一步

下一步应做 `Mainline-Final-v1 9B confirmation`，但必须使用本轮统一指标口径：Decision Health 只作 health check，主指标是 Support Quality、Hard-Negative Lifecycle、Criterion Grounding、Report Hygiene 和 Recovery Effectiveness。不要继续新增 runtime controller，也不要硬调 accept/reject 阈值。
