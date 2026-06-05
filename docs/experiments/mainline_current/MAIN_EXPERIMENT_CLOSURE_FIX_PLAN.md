# 主试验前收口修复计划

## 当前判断

最新 `EVIDENCE_EMPIRICAL_STRUCTURING_V1_FULLTEST39_4B` 证明 evidence formation 已经有实质进展：real / non-abstract / empirical strong support 明显上升，且 fallback strong support 仍为 0。但这轮还不能作为正式主试验，因为 final decision、指标口径和 pipeline 边界仍未冻结。

## 必须先修的硬问题

1. **指标口径修正**：`evidence_json_parse_errors=188` 是错误命名/错误聚合。正式报告应区分 `evidence_json_status_turn_count`、`evidence_json_invalid_or_missing_count` 和 `evidence_json_fallback_used_count`。
2. **gold label 口径修正**：不能再从 `pred + correct` 的不完整分支推断出 `unknown`。正式分析必须优先读取 gold 字段；没有 gold 字段时才使用 `accept_reject_correct` 反推。
3. **旧 controller 污染暴露**：当前 run 仍有 `sticky_recovery_bias` / `progression_gate_override` / `progression_gate_triggered`。正式主线必须明确禁用或明确声明保留。
4. **decision policy 与测试对齐**：当前 final decision 只作为保守 health check；单个 claim 的重复 strong support 不能直接触发 accept。测试已同步到该口径。
5. **support quality 继续拆细**：`figure/table` 不能无条件等价于 empirical result。下一轮 support quality audit 应拆分 `framework_diagram`、`method_figure`、`result_table`、`ablation_table`。

## 本轮已开始的修复

- `scripts/analyze_mainline_final_v1.py` 增加 gold / prediction / evidence JSON status / legacy controller 统计。
- `tests/test_review_decision_hygiene.py` 与当前保守 health-check policy 对齐，并新增 two-claim empirical support accept 测试。
- `sticky_recovery_bias` 与 `progression_gate_override` 已从 mainline runtime 默认关闭，只保留为 controlled ablation helper。

## 下一步唯一建议

先做 **Mainline-Final-v1 Clean Dry Run**，不要继续新增模型机制。旧 controller 已默认关闭，下一步应跑 4B fulltest39 clean dry run，确认 `sticky_recovery_bias`、`progression_gate_override` 和 `progression_gate_triggered` 均为 0，再决定是否进入 9B confirmation。

## 暂时不做

- 不做 sticky / throttle / progression gate 新版本。
- 不调 final decision 阈值。
- 不把 criterion 维度直接接入 accept/reject。
- 不开正式 9B 主试验。
