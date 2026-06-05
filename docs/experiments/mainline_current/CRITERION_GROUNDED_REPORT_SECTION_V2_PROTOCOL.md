# Criterion-Grounded Report Section v2 Protocol

本轮是离线 report rendering，不改 runtime、不改 final decision、不重跑模型。

## 目标

使用 `Criterion Grounding Linker v1` 的 state-grounded evidence/flaw 绑定结果，重渲染 final report 中的 criterion section。

## 规则

- 有正向 linked evidence 的维度写为 `positive_grounded`。
- 有 linked flaw / negative evidence 的维度写为 `negative_grounded`。
- 正负都有时写为 `mixed_grounded`。
- 没有 state grounding 的维度写为 `not_assessable`，并明确不能作为 paper weakness。

## 边界

本轮只改善报告可读性和 grounding 可诊断性，不改变 accept/reject。
