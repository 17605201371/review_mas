# Final Recommendation Policy v2 Execution Plan

## 目标

基于当前 fulltest39 离线审计结果，冻结一版更安全的 final-view 推荐口径。该口径不改变 runtime、不修改 live `ReviewState`，只用于论文结果层和 case 分析。

## 背景结论

- runtime binary decision 仍是 39/39 reject，只能作为 health check。
- Evidence Binding 已稳定：fallback/unbound strong support 为 0。
- 单纯 support-quality rule 可恢复部分 accept，但会引入 false accept。
- flaw 层主要是 fallback/meta 与 ungrounded candidate，只有少量 grounded major/critical flaw。
- unresolved/gap 主要是 targetless/stale/system burden，不能直接当作 confirmed paper weakness。

## 执行步骤

1. 使用已对齐 gold label 的 fulltest39 lifecycle/support summary 作为唯一输入。
2. 将 support-quality 正向信号从 `accept_like` 降为 `borderline_positive`，除非后续人工核查证明无 hard-negative 风险。
3. 只有 grounded major/critical flaw 允许输出 `reject_like`。
4. targetless unresolved 或证据不足输出 `not_assessable`。
5. stale/meta burden 输出 `borderline_insufficient` 或在 rationale 中解释，不写成 paper weakness。
6. 输出 V2 policy、逐样本 final-view table 和执行结论。

## 禁止事项

- 不改 runtime prompt。
- 不改 final decision 阈值。
- 不做 live state hygiene mutation。
- 不回 sticky / throttle / progression gate。
- 不把 novelty/soundness/empirical adequacy 裸接入 binary decision。
