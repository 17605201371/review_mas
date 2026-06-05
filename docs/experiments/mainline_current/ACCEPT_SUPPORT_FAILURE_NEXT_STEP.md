# Accept Support Failure Next Step

## 当前判断

final-view lineage 证明 payload-to-state 有明显损失，但 accept 样本本身在 payload 层仍没有足够 positive support。因此下一步不应把 lineage support 直接接入 decision，也不应调 accept 阈值。

## 下一刀

建议做 `Accept-Side Evidence Formation Audit / Context v2`：只围绕 gold accept 论文，检查 Evidence Agent 的 target claim 是否覆盖核心贡献、是否需要更好的 result/table/method snippet selection，以及是否需要让 Evidence Agent 对同一真实 claim 输出多条独立支持。仍然先离线/小样本，不做全局 decision 改动。
