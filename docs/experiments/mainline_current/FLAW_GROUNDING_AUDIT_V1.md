# Flaw Grounding Audit v1

## 结论

当前 flaw lifecycle 仍不足以支撑 final-view decision。主要问题不是 flaw 太少或太多，而是 flaw 的状态、证据绑定和来源没有足够区分：

1. fallback/meta flaw 仍可能以 major candidate 形式存在；
2. 部分 flaw 只绑定 positive/neutral evidence，不能作为负向 blocker；
3. candidate grounded flaw 与 confirmed grounded flaw 的边界不清；
4. dangling evidence reference 会让“看似 grounded”的 flaw 实际不可验证。

因此，下一步不应简单把 flaw count 接入决策，而应先建立 `paper_grounded_negative_flaw` 与 `meta/fallback/system limitation` 的 final-view 分类。

## 最小后续实现方向

仍建议先离线，不改 runtime：对每个 flaw candidate 派生 `flaw_grounding_status`、`flaw_source_type`、`criterion_linked_dimension`、`negative_evidence_ids`，并只允许 confirmed + paper_grounded + negative_evidence 的 flaw 作为强 blocker。
