# Final-View Hygiene Fix v1 Plan

## 目标

本轮只修 2.1-2.5 中能安全落地的缺陷：final decision / final report 前的派生视图污染，而不是 live state 轨迹。

## 修复范围

1. targetless unresolved 不再作为 paper defect blocker，进入 final-view 时降级为 `decision_view_targetless_uncertainty`。
2. fallback/meta flaw 的识别从 `flaw-fallback` 和 `source=fallback` 扩展到 `fallback-extraction`、`fallback_unverified`、system/meta 文本。
3. final report strengths 只渲染 real-claim-bound strong support，避免 fallback/unbound support 被写成优势。
4. criterion 与 weakness 渲染过滤 fallback/meta flaw，避免系统限制进入审稿维度 weakness。

## 不修的范围

本轮不调 accept 阈值、不改 manager、不改 recovery controller、不改 live `_refresh_state_consistency()`。原因是这些改动会改变推理轨迹，风险高于收益。
