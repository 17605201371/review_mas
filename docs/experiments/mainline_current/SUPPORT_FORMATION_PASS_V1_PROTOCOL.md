# Support Formation Pass v1 协议

## 背景

前几轮 Evidence Context / Evidence Binding / Final-View Hygiene 说明：系统并非完全不能形成正向证据，但在进入 flaw / recovery / final 之前，真实 claim 上的 strong support 经常不足。最终 always-reject 的一部分原因是 positive support 还没充分形成，后续负面状态和 final-view 再怎么清理，也缺少足够正向支撑。

## 本轮目标

Support Formation Pass v1 只做一个轻量运行时调整：当系统准备进入 `analyze_flaws`、`request_evidence_recheck`、`challenge_previous_hypothesis`、`summarize_progress` 或 `finalize` 等 support-sensitive 动作，但当前 real-claim strong support 仍不足时，插入一次普通 `verify_evidence`。

目标不是直接改 accept/reject 阈值，也不是硬性让系统 accept，而是先给 Evidence Agent 一次补充正向证据的机会。

## 触发条件

Support Formation Pass 触发条件为：

- 当前 action 属于 support-sensitive action。
- `verify_evidence` 当前允许执行。
- `ReviewState` 中已有 claim。
- real-claim strong support 少于 2。
- 最近 evidence verification 次数少于 2。
- 上一轮不是 `support_formation_override`，避免连续循环。

## 行为

触发后，manager payload 会被改为：

- `action_type = verify_evidence`
- `effective_action_type = verify_evidence`
- `turn_mode = normal_evidence`
- `phase = normal_review`
- `policy_source = support_formation_override`

同时 turn log 会记录：

- `support_formation_pass_triggered`
- `support_formation_pass_reason`
- `support_formation_pass_from_action`

## 明确不做的事

本轮不改：

- final decision 阈值
- recovery / sticky / throttle / progression gate
- validator / lifecycle
- fallback 生成逻辑
- evidence binding 规则
- final-view hygiene 规则

## 实验口径

正式结论只使用 `max_turns=8` 的同口径结果：

- baseline: `outputs/results_main/review_infer/support_quality_v1_mixed16.jsonl`
- candidate: `outputs/results_main/review_infer/support_formation_pass_v1_mixed16_mt8.jsonl`

早期 `support_formation_pass_v1_mixed16.jsonl` 使用 `max_turns=5`，只作为辅助记录，不作为正式结论。
