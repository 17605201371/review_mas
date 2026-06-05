# Negative Evidence Anchor Confirmation Pass v1 Protocol

## 定位

本轮只在 10 条 diagnostic subset 上做 4B 小跑，不改 runtime、不写回 ReviewState、不接 final decision。

## 目标

验证 `Negative Evidence Anchor Extraction v1` 抽出的 table/result/baseline/ablation anchors 是否能支撑更高精度的 negative blocker confirmation。

## 约束

- 模型只能使用 `paper_anchors`。
- blocker 必须引用真实 `claim_id` 和一个 `anchor_id`。
- 不允许把 missing context / excerpt limitation / absent table visibility 当 paper flaw。
- trusted blocker 还要通过后处理：real claim、core criterion、quant anchor、confidence >= 0.6、非 meta。
