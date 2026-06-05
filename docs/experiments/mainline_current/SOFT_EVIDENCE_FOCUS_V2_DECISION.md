# Soft Evidence Focus v2 Decision

## 结论

`Soft Evidence Focus v2` 建议保留为当前 4B mainline candidate 的 evidence-side 组件。

理由是：它在关闭 sticky / progression gate 等旧 controller 的干净主线上，恢复了高质量正向 evidence formation：`real_strong=40`、`nonabstract=39`、`empirical=33`，且 `fallback_strong=0`、`legacy_controller_active_turns=0`。这比 Context v2 和 hard Focus v1 都更接近主试验所需的 evidence formation 能力。

## 相比 hard Focus v1 的关键改进

hard Focus v1 证明 accept 样本需要 target narrowing，但 top-2 hard truncation 压缩了全局 support。Soft Focus v2 改成 preferred ordering 后，全局 real/non-abstract/empirical support 明显回升，patch emitted / committed 也回升，说明“轻量偏置”比“硬约束”更适合当前系统。

## 仍然存在的问题

- runtime final decision 仍不可信：本轮 `pred_accept=1`，且 `NnExMNiTHw` 是 false accept；9 个 gold accept 仍未恢复 runtime accept。
- evidence JSON invalid/missing 变高：`31`，虽然 fallback used 仍为 0，但需要在后续 JSON robustness / output discipline 中继续监控。
- broad target turns 仍高：`207`，说明 focus 是软偏置，不是 target sanitize 修复；这不应再用 sticky/throttle/gate 解决，而应在 Evidence observation / criterion-grounded recommendation 层处理。

## 下一步

下一步不继续调 controller，也不直接调 accept/reject 阈值。建议做：

1. `Soft Focus v2 + Final Recommendation Calibration` 离线复算，检查 false accept `NnExMNiTHw` 是否能被 high-precision / hard-negative policy 拦住。
2. 对 Soft Focus v2 运行 support quality + hard-negative audit，确认新增 empirical support 是否独立、是否集中于少数 claim、是否伴随 grounded flaw。
3. 如果离线 recommendation policy 能保留 support 增益并挡住 false accept，再将 `Soft Evidence Focus v2` 写入 `MAINLINE_FINAL_V1_SPEC.md` 的候选 runtime 组件。

## 暂不做

- 不恢复 sticky / throttle / progression gate。
- 不做 live state hygiene mutation。
- 不把 runtime binary final decision 当主指标。
- 不把 low novelty / weak empirical adequacy 直接裸接入 accept/reject。
