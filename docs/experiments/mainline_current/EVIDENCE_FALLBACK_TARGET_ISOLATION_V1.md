# Evidence Fallback Target Isolation v1

## 背景

本轮目标不是继续增加 controller，而是检查 Evidence Agent 的结构化证据链路里是否仍存在 fallback 污染。审计对象包括 `evidence_json_robustness_v1_1_mixed16`、`decision_hygiene_view_v1_fulltest39_4b`、`integrated_mainline_4b_fulltest39` 与 `evidence_binding_v1_mixed16`。

## 审计结论

Evidence Binding v1 已经让 state 层不再把 fallback / unbound strong support 当作真实 strong support，但 Evidence Agent 的输入层仍有一个污染入口：当 manager target 是 `claim-fallback-*` 时，Evidence State Slice 会把 fallback claim 暴露为 `target_claims`。虽然 `allowed_claim_ids` 会过滤掉 fallback ids，模型仍会看到 fallback claim 正文，并可能继续生成绑定到 fallback claim 的 evidence。

这类 evidence 多数会在 state merge 时被降权，不会直接计入 real strong support，但它会浪费 Evidence turn，并增加 fallback evidence、unresolved、critique fallback 与后续噪声。

## 关键统计

- `evidence_json_robustness_v1_1_mixed16`: Evidence turn fallback targets 5 次，涉及 2 个样本；Evidence Agent 输出 fallback-bound strong payload 2 条。
- `decision_hygiene_view_v1_fulltest39_4b`: Evidence turn fallback targets 72 次，涉及 16 个样本；Evidence Agent 输出 fallback-bound strong payload 26 条。
- `integrated_mainline_4b_fulltest39`: Evidence turn fallback targets 18 次，涉及 9 个样本；Evidence Agent 输出 fallback-bound strong payload 7 条。
- `evidence_binding_v1_mixed16`: Evidence turn fallback targets 39 次，涉及 8 个样本；Evidence Agent 输出 fallback-bound strong payload 4 条。

## 本轮修复

在 `agent_system/environments/env_package/review/state.py` 的 `_render_evidence_state_slice(...)` 中做最小修复：

- Evidence Agent 的 `target_claims` 只暴露真实 claim。
- `allowed_claim_ids` 只来自真实 claim。
- `claim-fallback-*` 不再作为 Evidence Agent 可验证目标暴露。
- 被剔除的 fallback target 记录到 `fallback_claim_targets_omitted`，便于后续审计。

这个改动不改变 final decision，不改变 recovery，不改变 fallback claim 生成，也不改变 state merge 的 binding validator。

## 验证

通过针对性测试：

```text
PYTHONPATH=. /opt/conda/envs/DrMAS-qwen35/bin/python -m pytest -q tests/test_review_inference_runner.py::test_evidence_observation_omits_fallback_claim_targets tests/test_review_decision_hygiene.py tests/test_review_multiturn.py
16 passed
```

全量 `tests/test_review_inference_runner.py` 当前仍有 5 个既有 manager-policy 测试失败，集中在 progression/throttle 预期与当前代码行为不一致；这些不是本轮 Evidence slice 修复引入的，不在本轮修改范围内。

## mixed16 验证结果

已在 4B mixed16 上完成验证。按标准分析脚本口径，`evidence_fallback_payload_count = 7`，`strong_support_on_real_claim = 5`，`strong_support_on_fallback_claim = 0`，`strong_support_binding_precision = 1.0`。补充审计显示，相比 `evidence_json_robustness_v1_1_mixed16`，state fallback-bound evidence 从 5 降到 1，payload fallback-bound evidence 从 6 降到 3，payload model fallback strong 从 2 降到 0。

同时，本轮没有提升 positive support formation：`rows_with_2plus_real_strong_support` 仍为 0。因此它应作为 Evidence 输入卫生补丁保留，而不是作为最终性能提升结论。

## 当前决策

保留 Evidence Fallback Target Isolation v1。下一步不要恢复 support-pass、sticky、throttle 或 final decision 阈值硬调；应继续沿 Evidence 质量主线验证 fulltest39，并分析 non-abstract / empirical / independent support 形成不足的问题。
