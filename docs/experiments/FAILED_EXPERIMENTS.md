# Failed Experiments — 负面结果汇总

所有 **mainline 上实施但被证明不改善或恶化 reward 的改动**。
行为代码均已回滚；文档保留作为"不要重做"的证据。

---

## 1. p25.1 progression_gate_v1 — 强 gate 误伤

**时间**: 2026-04-23
**原文**: [archive/progression_gate_v1/](archive/progression_gate_v1/)

### 想法

当 target 是 `fallback_target` / `broad_target` / `weak_conflict` 时，阻断 aggressive recovery（强制用 `verify_evidence` / `analyze_flaws` 替代）。

### 结果

- Layer 3 结果塌缩，多个样本 reward 下降
- 伴随 max_turns 配置污染问题（早期 finalize 被阻）
- 详见 [archive/progression_gate_v1/P25_1_PROGRESSION_GATE_V1_COMPARE.md](archive/progression_gate_v1/P25_1_PROGRESSION_GATE_V1_COMPARE.md)
- 失败分析 [archive/progression_gate_v1/P25_1_PROGRESSION_GATE_V1_FAILURE_REVIEW.md](archive/progression_gate_v1/P25_1_PROGRESSION_GATE_V1_FAILURE_REVIEW.md)

### 为什么失败

粗启发（fallback/broad/weak_conflict 三个布尔标签）信号太粗，把系统拦进死循环。

### 处置

回滚；保留 `_progression_gate_issues` 逻辑但默认**不激活**（代码存在但用更严的条件门控）。

---

## 2. Recovery Entry Decision v1 — defer non-ready sticky push

**时间**: 2026-04-24
**原文**: [archive/tqc_and_red_v1/RECOVERY_ENTRY_DECISION_V1_RESULT.md](archive/tqc_and_red_v1/RECOVERY_ENTRY_DECISION_V1_RESULT.md)

### 想法

基于 TQC 观察数据（89.5% push 在非 ready 状态），在 `apply_manager_policy_fallback` 的 sticky 之后加条件：

```
IF policy_source == sticky_recovery_bias
   AND action == challenge_previous_hypothesis
   AND readiness ∈ {not_ready_for_recovery, fallback_bridge_only}:
       → defer 到 analyze_flaws 或 verify_evidence
```

### 结果（10 样本 Layer 3）

| 指标 | B (TQC obs only) | C (Entry Defer) | C − B |
|---|---|---|---|
| Mean reward | 0.6251 | 0.6146 | **−0.0105** |
| Decision correct | 9/10 | 9/10 | 0 |
| W / T / L | — | — | 0 / 9 / 1 |
| `hj323oR3rw` | 0.3755 | 0.2705 | **−0.105** |

- Defer 触发 3 次（`hj323oR3rw` 1, `qgyF6JVmar` 2）
- 其中 2 次被下游 `apply_finalize_policy` 吞掉
- 1 次被重新推回 `challenge_previous_hypothesis`
- 9/10 样本未变化；唯一变化样本恶化

### 为什么失败

1. **defer 没有等价内容建设**：sticky 的非 ready push 虽对象错，但 state update / dialogue 累积对最终 report 有副作用收益
2. **下游 override 吞掉 defer**：finalize / conflict_block 链路覆盖
3. **defer 太窄**（仅 `not_ready` + `fallback_bridge`），大量 `needs_target_refinement` / `needs_evidence_grounding` 未触发；扩大后很可能误伤更多

### 处置

**行为代码已回滚**（commit `e1f8f1e`）；保留：
- TQC observability 5 维诊断
- `recovery_entry_deferred` 等字段（默认 False，log schema 兼容）
- 本文档作为负面证据

---

## 3. p25.2 ~ p25.5a 系列（历史负面）

**原文**: [archive/tqc_and_red_v1/NEGATIVE_FINDINGS_p25_2_to_p25_5a.md](archive/tqc_and_red_v1/NEGATIVE_FINDINGS_p25_2_to_p25_5a.md)

### 涉及变体

- **p25.2** sticky 新版本
- **p25.3** throttle 变体
- **p25.4** fallback global restraint
- **p25.5a** more aggressive sticky

### 共同失败模式

"拦掉旧路径，但没建新路径" — 与 progression_gate_v1 / Recovery Entry Decision v1 相同的模式。

### 处置

所有代码已不在主线；文档作为历史参考。

---

## Do Not Retry 列表

基于上述三批失败，**以下方向不应再尝试**：

| 方向 | 为何不要再做 |
|---|---|
| progression_gate / throttle / gate 任何变体 | 粗启发 + 阻断路径 = 塌缩 |
| 任何 sticky 新版本或扩展 | sticky 本身不是问题根源；约束它会损伤副作用收益 |
| fallback target 全局 suppress | fallback 是系统应急机制，全局 suppress 让系统停转 |
| 基于 "阻断 recovery 的简单规则" | 已试过粗启发（progression_gate）和精细信号（TQC defer），都失败 |
| 同时改动多个 controller | memory 原则：单 controller 只在有净增益时保留 |

---

## 共同教训

1. **识别问题 ≠ 阻断问题**
   TQC 能精准识别 "89.5% push 在非 ready 状态"，但 defer 这些 push 不是解法。系统缺的不是"更强 gate"，而是"更好的建设机制"。

2. **副作用收益真实存在**
   看似"错的 recovery" 仍有 side effect（state update / dialogue）对 final report 贡献不可忽略。单纯减少错误 recovery 会一起减掉这部分收益。

3. **下游 override 链路复杂**
   Mid-policy 的 action 改动经常被 `apply_finalize_policy` / `conflict_block_override` 等下游吞掉或覆盖。单点 defer 难以稳定控制最终 action。

4. **小样本单样本波动大**
   10 样本 forensic subset 中 1 个样本的极端恶化（`hj323oR3rw` -0.105）能淹没 9 个 tie。需要更大样本或控制变量才能做更强结论。

---

## 如何避免重蹈覆辙

提出新 controller 前，**先对照本文档检查**：

- 是否属于 "阻断/defer" 模式？→ 可能再次失败
- 是否依赖粗启发？→ 可能误伤
- 是否有"建设性替代路径"？→ 没有就停手
- 是否独立可测试？→ 没有就拆到最小
- 小样本 W/T/L 是否至少 3:7:0？→ 否则不要合并

---

## 当前主线（保留的部分）

```
p25.1 baseline + explicit recovery phase
+ flaw_fix_v2 bug 修复 (+0.0417 验证)
+ TQC observability 5 维诊断 (无行为改动)
```

Mean reward (Layer 3 10 样本): **0.6251** | Decision correct: **9/10**

详见 [POSITIVE_EXPERIMENTS.md](POSITIVE_EXPERIMENTS.md)。
