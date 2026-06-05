# Evidence Lineage Support View v1 Decision

## 结论

保留为离线 final-view / audit 层，不进入 live state merge。payload lineage 证明 Evidence Agent 已经形成过比 final ReviewState 更多的 real strong support；但直接用 lineage support 作为 accept 规则仍会产生 false accept 风险。

## 下一步

下一步应把 lineage support view 与 criterion grounding / final-view hygiene 结合，形成报告与诊断层；暂时不要把它接入 runtime accept/reject。更具体地说，应做 `Final-View Evidence Lineage Report v1`，展示哪些正向证据被 final state 压缩掉，并辅助论文分析 support formation loss。
