# Fallback Flaw Lifecycle Guard v1 Next Step

## 当前结论

`Fallback Flaw Lifecycle Guard v1` 应保留，但它只是安全修复，不是主试验前最后一刀。

最新 fulltest39 的 blocker 分布：

| blocker family | gold accept | borderline positive |
| --- | ---: | ---: |
| hard_negative_burden | 5 | 3 |
| method_soundness_gap | 3 | 1 |
| support_depth_gap | 1 | 1 |

## 下一步唯一建议

下一步做 **Final-View Hard-Negative / Unresolved Lifecycle Simulation v1**，先离线，不改 runtime。

原因：

1. gold accept 中 `hard_negative_burden=5` 是当前最大阻塞项。
2. method/soundness 缺口也存在，但如果 unresolved / trusted hard-negative 仍然把样本压成 reject，先补 method evidence 可能无法转化为 accept-like。
3. runtime final decision 仍是 39 reject，应继续作为 health check，不应直接调阈值。

## 具体要回答

- `unresolved_gt4` 是真实 paper risk，还是系统未关闭的 stale/open item？
- `trusted_major_or_critical_flaw_present` 是否真的 grounded、confirmed、paper-level？
- 哪些 gold accept 只需要 final-view unresolved cleanup 就能变成 `borderline_positive` 或 `accept_like`？
- 哪些样本必须补 method/soundness evidence formation？

## 暂时不做

- 不放宽 high-precision accept-like。
- 不恢复 sticky / throttle / progression gate。
- 不把 novelty/soundness 直接裸接入 decision。
- 不把 hygiene 放回 live state mutation。
