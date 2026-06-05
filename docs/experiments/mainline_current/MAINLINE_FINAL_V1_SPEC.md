# Mainline-Final-v1 Spec

## 目标

`Mainline-Final-v1` 是论文主试验前的收口版本，用于把已经验证为正向或必要的模块固定下来，并把失败分支排除出主线。该 spec 的目标不是继续增加新 controller，而是保证后续 fulltest / 9B confirmation 结果可复现、可解释、可写入论文。

## Runtime 主线模块

进入 runtime 主线的模块只包括：

1. `p25.1 + explicit recovery phase` 保留版。
2. Evidence Binding Robustness：真实 claim 白名单绑定、fallback/unbound strong support 降权或隔离。
3. Evidence JSON Contract / JSON Robustness：降低 Evidence Agent JSON parse/fallback 污染，并把 parse status 写入 turn log。
4. Evidence fallback target isolation v1.1：Evidence Agent 不把 `claim-fallback-*` 当成 primary target；fallback-only target 用真实 claim 候选替代。
5. Evidence ID Turn-Scoping v1：把 Evidence Agent 每轮复用的 `evidence-1` / `evidence-2` 改成 turn-scoped id，避免跨 turn evidence merge 覆盖。
6. Evidence Context Selection v2：Evidence Agent 使用 wrapper-cleaned、section-aware evidence context，优先暴露 method/results/table/conclusion 片段。
7. Soft Evidence Focus v2（候选）：Evidence Agent 保留最多 4 个真实 claim，但把 top-2 high-importance / empirical / unsupported claim 标记为 preferred，而不是硬截断 target。该模块已通过 4B fulltest39 证明 support formation 明显提升，但仍需 final recommendation calibration 兜住 false accept。
8. Config alignment / observability：固定 `max_turns`、model、subset、max_model_len、max_tokens、seed、batch 等关键参数，并保留 run config。

## Offline / Final-View 模块

这些模块只作为 derived view、report rendering 或审计层，不改 live `ReviewState`：

1. Final-view hygiene / decision health analysis。
2. Support quality / evidence independence audit。
3. Criterion coverage & grounding audit。
4. Criterion-grounded report section。
5. Final-view flaw lifecycle / meta-leakage classification。
6. Final-view invalid binding / support-quality filter：只在分析视图中区分 valid real support、invalid-bound support、fallback/unbound support，不修改 live `ReviewState`。

## 明确不进入主线的分支

以下方向已暂停，不进入 `Mainline-Final-v1`。代码中保留为 controlled ablation helper，但 runtime 默认关闭：

1. sticky 系列。
2. throttle / progression gate 系列。
3. recovery entry defer。
4. live state hygiene mutation。
5. global fallback suppression。
6. Support Formation Pass runtime controller。
7. hard top-2 Evidence Focus v1：证明 target narrowing 有价值，但硬截断会压缩全局 support，不进入主线。
8. medium support 直接升级为 strong 的 final decision 规则。
9. final decision 阈值硬调。
10. runtime Evidence Claim Binding Guard v1：fulltest39 证明 live 清空 invalid `claim_id` 会压缩 accept-side support formation，因此不保留。

## Final decision 定位

`accept/reject` 不作为唯一主指标，只作为 health check。论文主指标应同时报告：

- evidence binding quality；
- Evidence JSON/fallback robustness；
- positive support formation；
- support quality / evidence independence；
- state hygiene；
- recovery effectiveness；
- criterion coverage / grounding；
- flaw lifecycle / meta-leakage；
- decision collapse / always-reject health check。

## Report rendering 原则

final report 应避免把系统限制写成论文缺陷：

- excerpt / truncation / missing full text 放入 `Review Limitations` 或 `Not Assessable`；
- fallback / malformed JSON / recovery failure artifact 不进入 `Key Weaknesses`；
- ungrounded candidate flaw 进入 `Potential Concerns`，不等同 confirmed weakness；
- only grounded confirmed major/critical flaws 才能作为强 reject blocker 的证据。

## 当前 dry-run 数据源

当前主线材料来自多个阶段，不能混用为单一最终数字：

1. 早期 4B retained bundle：用于说明 final decision collapse、final-view hygiene 和 report-layer 问题。
2. 9B fulltest39 rerun：用于 criterion grounding / report quality / support-quality 论文分析。
3. 4B `Evidence ID Turn-Scoping v1` fulltest39：用于验证 evidence retention bug 和 invalid binding 的后续暴露。
4. `Final-View Invalid Binding Filter v1`：基于 ID-scoped fulltest39 的离线 support-quality 视图，不是 runtime 决策规则。

当前统一结论：`accept/reject` 仍只作为 health check；论文主结果应报告 evidence retention、binding quality、support quality、criterion grounding、final-view flaw lifecycle 和 failure taxonomy。若后续继续跑实验，只做最终确认或复现实验，不再新增 controller 分支。

## 2026-05-02 收口修正

`sticky_recovery_bias` 与 `progression_gate_override` 已从 mainline runtime 默认关闭，只保留为代码中的 ablation helper。后续 clean dry run 应检查 `policy_source_counts` 中这两个来源为 0；若需要复现实验分支，必须显式打开对应常量并单独标注文档。

## 2026-05-02 Evidence-side candidate update

`Evidence Context Selection v2` 与 `Soft Evidence Focus v2` 已成为当前 evidence-side 主线候选。4B fulltest39 的 Soft Focus v2 结果为 `real_strong=40`、`nonabstract=39`、`empirical=33`、`fallback_strong=0`、`legacy_controller_active_turns=0`，说明软偏置可以在不恢复旧 controller 的情况下恢复正向 evidence formation。风险是 runtime false accept `NnExMNiTHw` 与 evidence JSON invalid/missing 增加，因此正式主试验前必须接 `Final Recommendation Calibration / Hard-Negative Audit`，runtime binary final decision 仍只作为 health check。
