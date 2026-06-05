# Accept-Side Evidence Focus v1 Decision

## 结论

`Accept-Side Evidence Focus v1` 暂不作为 mainline replacement 保留，但保留为下一轮 `Soft Evidence Focus v2` 的依据。

## 为什么不直接保留

Focus v1 证明“accept 样本需要更窄、更核心的 evidence target”这个判断是对的：gold accept 的 broad target turns 下降，payload real strong 和 rows with 2+ real strong 都上升。

但当前实现是 top-2 hard focus，会把 Evidence Agent 的 allowed claim_ids 直接压窄到两个 claim。结果是：accept 侧变好，但全局 support formation、evidence turns、patch emission 都下降。这不适合作为正式主线，因为论文主试验需要同时保留 reject 样本上的 evidence exploration 和 hard-negative grounding。

## 保留的有效结论

- `Evidence Context Selection v2` 应进入候选主线：它更稳定地提升全局 real/non-abstract support，并减少 JSON fallback / unresolved / gap。
- `Accept-Side Evidence Focus v1` 证明 target narrowing 有价值，但 hard top-2 太激进。
- Focus v1 新增的 `evidence_focus_*` 日志字段已补入 `build_turn_log`，后续运行可以直接统计 focus 是否真实生效。

## 下一刀

建议实现 `Soft Evidence Focus v2`，只做 evidence observation 层的软偏置：

1. 保留 3-4 个 allowed real claims，不再硬截断为 top-2。
2. 将 top-2 high-importance / empirical / unsupported claims 排在前面，并标记为 `preferred_claim_ids`。
3. prompt 要求优先抽 preferred claims，但允许在其他 allowed claims 上输出高质量 empirical evidence。
4. 明确要求每条 evidence 记录 `support_focus_role = preferred | secondary`，便于分析 accept support 是否来自核心 claim。

## 暂不做

- 不恢复 sticky / throttle / progression gate。
- 不调 final decision 阈值。
- 不把 abstract medium support 直接升为 strong。
- 不做 live state hygiene mutation。
- 不把 Focus v1 的 hard top-2 直接并入正式主线。
