# Recovery Entry Decision v1 — 负面结果报告

## 动机

TQC Layer 3 审计发现：
- 60 turns 中 89.5% 的 recovery push 发生在非 ready 状态
- sticky_recovery_bias 15/15 推进**全部**在非 ready 状态
- 非 ready push 次数与 reward 负相关（最低 reward 样本 hj323oR3rw 有 5 次非 ready push）

基于此提出最小行为改动：

```
IF policy_source == sticky_recovery_bias
   AND action == challenge_previous_hypothesis
   AND recovery_readiness_label ∈ {not_ready_for_recovery, fallback_bridge_only}:
       → defer 到 analyze_flaws（evidence 存在且无 flaws 时）或 verify_evidence
```

仅约束 sticky；不动 `evidence_progress_override`、`conflict_block_override` 等其它来源。

## 三方对比（10 样本）

| paper_id | A_base | B_tqc_obs | C_entry_defer | C−B | dec_C |
|---|---|---|---|---|---|
| 2Cg4YrsCMA | 0.5864 | 0.6122 | 0.6122 | +0.0000 | 1 |
| 9EBSEkFSje | 0.6890 | 0.7420 | 0.7420 | +0.0000 | 1 |
| EXGahWDp1E | 0.6979 | 0.6439 | 0.6439 | +0.0000 | 1 |
| IqaQZ1Jdky | 0.6305 | 0.6781 | 0.6781 | +0.0000 | 1 |
| NhLBhx5BVY | 0.5854 | 0.5159 | 0.5159 | +0.0000 | 1 |
| Ze49bGd4ON | 0.5141 | 0.6791 | 0.6791 | +0.0000 | 1 |
| **hj323oR3rw** | 0.2952 | 0.3755 | **0.2705** | **−0.1050** ↓ | 0 |
| kdriw2a8sl | 0.6919 | 0.7169 | 0.7169 | +0.0000 | 1 |
| meY36sGyyv | 0.5911 | 0.6334 | 0.6334 | +0.0000 | 1 |
| qgyF6JVmar | 0.6415 | 0.6537 | 0.6537 | +0.0000 | 1 |
| **MEAN** | **0.5923** | **0.6251** | **0.6146** | **−0.0105** | 9/10 |

**Win / Tie / Loss (C vs B) = 0 / 9 / 1**

A = p25.1 baseline（iter_recovery_phase_v1）
B = TQC observability only（前一步 commit）
C = + Recovery Entry Decision v1 defer 行为

## Defer 触发统计

- Total defers: 3
- By readiness reason: `{not_ready_for_recovery: 3}`
- Per sample: `{hj323oR3rw: 1, qgyF6JVmar: 2}`
- Final action_type after defer:
  - `finalize`: 2 （defer 被下游 auto-finalize 覆盖）
  - `challenge_previous_hypothesis`: 1 （defer 被后续 sticky / conflict_block 再推）

## Readiness 分布变化（B → C）

| label | B | C | 变化 |
|---|---|---|---|
| ready_for_aggressive_recovery | 2 | 2 | — |
| needs_target_refinement | 11 | 11 | — |
| needs_evidence_grounding | 15 | 15 | — |
| fallback_bridge_only | 2 | 2 | — |
| not_ready_for_recovery | 30 | 27 | −3（等于 defer 次数） |
| **Total turns** | 60 | 57 | −3（episode 提前结束） |

## Recovery push 变化（B → C）

- Total pushed turns: 19 → 13（−6）
- pushes on `not_ready_for_recovery`: 6 → **0** ✓ 达成意图
- pushes on `needs_target_refinement`: 5 → 5 （未约束）
- pushes on `needs_evidence_grounding`: 6 → 6 （未约束）

**Defer 在 `not_ready_for_recovery` 维度上生效**，但净 reward 下降。

## 诊断

1. **9/10 样本完全相同**：defer 条件严苛（仅 `not_ready`/`fallback_bridge`），触发少；且下游 `apply_finalize_policy` / `conflict_block_override` 在多数情况下把 defer 吞掉。
2. **hj323oR3rw 恶化（−0.105）**：该样本原本就是最差样本（唯一 dec=0），被 defer 的一次 sticky push 原本可能在最终 report 中累积了一些对 alignment 有利的内容；defer 后替代路径没产生等价输出。
3. **qgyF6JVmar 2 次 defer 但 reward 不变**：说明 defer 信号被下游覆盖，最终 action 仍是 recovery 或 finalize，对最终报告没实质影响。

## 结论

TQC 诊断层是**正确的**（证据见 `TQC_LAYER3_AUDIT.md`），但是 **"defer non-ready sticky push" 不是可行的最小行为改动**：

- 减少非 ready push 数量（6 → 0 on `not_ready_for_recovery` 轴），意图达成
- 但最终 reward 未改善，反而让最差样本进一步恶化
- 说明 sticky 的非 ready push 虽然对象不正确，但其 side effects（state update、dialogue 累积）对最终 report 贡献不可忽略
- 单纯退回 `verify_evidence` / `analyze_flaws` 没提供等价或更好的内容建设机制

这印证了 memory 中 "throttle / gate 容易误伤" 的经验，即便使用更精细的 TQC 信号也不例外。

## 论文价值

这是**一个强负面结果**，可以作为论文的重要实验材料：

> 即使使用 Target Quality Certificate 精确识别 recovery entry 的对象质量问题，简单"defer non-ready push"并不能改善整体表现。这证明问题不是"阻止错误的 recovery"，而是"**缺少正向的 target refinement / evidence grounding 机制**"。

## 产出文件

- `outputs/results_main/review_infer/p25_1_red_v1_l3.jsonl` — C 运行结果
- `outputs/results_main/review_infer/p25_1_tqc_v1_l3.jsonl` — B 运行结果（对比基准）
- `p25_1_red_v1_l3.log` — C 运行日志
- `scripts/analyze_tqc.py` — 分析脚本（含 Q6 defer 统计）
- 代码位置: `agent_system/review_manager_policy.py:1370-1431`（defer 逻辑）

## 状态（2026-04-24 更新）

**行为代码已回滚**：

- ✅ 保留：TQC observability（5 维诊断 + readiness 标签）
- ✅ 保留：`flaw_fix_v2` 相关的 bug 修复（+0.0417 mean 验证有效）
- ✅ 保留：本失败实验文档（作为负面证据）
- ✅ 保留：`recovery_entry_deferred` 等字段在 state.py（作 log schema 兼容，始终 False）
- ❌ 移除：`review_manager_policy.py` 中 defer 行为逻辑（原 line 1377-1431）

当前主线 = `p25.1 + explicit recovery phase + TQC observability + flaw_fix_v2`。

## 下一步方向（不再是 gate/defer）

TQC 数据表明，非 ready 状态的主体是 `needs_target_refinement` (11) 和 `needs_evidence_grounding` (15)，单纯 defer 无法建设新内容。推荐转向 **Readiness Repair / Target Refinement v1**：

| TQC label | 正向建设动作 |
|---|---|
| `needs_target_refinement` | 生成/选择更窄 target |
| `needs_evidence_grounding` | 明确 claim-evidence 对齐 |
| `fallback_bridge_only` | 把 fallback bridge 到真实 claim |
| `not_ready_for_recovery` | 进入 readiness repair, 而非 defer |
| `ready_for_aggressive_recovery` | 允许 aggressive recovery |

核心问题从"要不要拦 recovery"转为"target 不 ready 时系统应该建设什么"。
