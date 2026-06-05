# Evidence Context Selection v2 Protocol

## 背景

干净主线 `mainline_final_v1_clean_4b_fulltest39` 修掉了旧 controller 污染，但 9 个 gold accept 仍全部被 reject。accept-side 审计显示：

- gold accept 的 evidence turns 普遍是 broad target；
- payload 中 real medium 支持不少，但几乎都来自 abstract；
- non-abstract / empirical support 在 accept 样本上没有稳定形成；
- v1 context 日志里的 `contains_results/table` 可能来自 abstract 中的普通词，而不是真正的 Results/Table section。

因此这轮不调 final decision，不恢复 sticky/gate，不做 live state hygiene，只修 Evidence Agent 的输入上下文选择。

## 改动

`_render_evidence_context_with_meta(...)` 从 `section_aware_v1` 升级为 `section_aware_v2`：

1. `_clean_paper_body(...)` 保留换行，避免 section header 被空白归一化抹掉。
2. 优先匹配真实 section header，例如 `Method`、`Experiments`、`Results`、`Conclusion`。
3. 如果找不到真实 header，才在 abstract 之后做关键词 fallback。
4. 去重逻辑允许真实 section header 覆盖 abstract 窗口，避免 abstract 片段把 Method/Results 片段挤掉。
5. 日志字段继续使用既有 `evidence_context_*` 字段，`evidence_context_mode=section_aware_v2`。

## 不改内容

- 不改 final decision 阈值。
- 不改 sticky / throttle / progression gate。
- 不改 manager 总体架构。
- 不改 validator / lifecycle / reward。
- 不把 abstract medium support 直接升级成 strong。

## 评估重点

4B fulltest39 对比 clean baseline：

- accept 样本 real/non-abstract/empirical strong support 是否上升；
- fallback strong support 是否保持 0；
- evidence JSON fallback 是否不恶化；
- false accept 是否不明显增加；
- old controller 是否保持关闭。
