# Experiment Log — Mainline 实验流水账

项目时间线上所有 mainline 实验的按时间顺序记录。分支 `codex/p25-1-explicit-mainline`。

详细对照：
- 成功改动 → [POSITIVE_EXPERIMENTS.md](POSITIVE_EXPERIMENTS.md)
- 失败改动 → [FAILED_EXPERIMENTS.md](FAILED_EXPERIMENTS.md)
- 原始单文件文档 → [archive/](archive/)

---

## 时间线概览

| 时期 | 阶段 | 关键结论 |
|---|---|---|
| p25.0 | 基线建立 + 初次 patch | model decision 固定 Qwen3.5-9B; frozen compare setup 建立 |
| p25.1 setup | 10 样本 forensic subset 构建 | iteration subset 和 pairwise case table 成型 |
| p25.1 progression_gate_v1 | 第一次 controller 尝试 | **失败** —— 强 gate 容易误伤 |
| p25.1 forensic v2 | target 质量 / recovery push 溯源 | 发现 `sticky_recovery_bias` 是非 ready 推送主因 |
| p25.1 flaw_fix_v2 | bug 修复批次 | **成功** —— mean +0.0417, W/T/L = 7/1/2 |
| p25.1 TQC v1 | Target Quality Certificate 观察层 | **成功** —— 89.5% push 在非 ready 状态的发现 |
| p25.1 Recovery Entry Decision v1 | defer 非 ready sticky push | **失败** —— mean -0.0105, 已回滚行为代码 |

---

## 1. p25.0 — 基线建立

**目标**：固定模型决策与 frozen compare 环境，为后续实验提供可复现基线。

**产出**：
- 固定模型：Qwen3.5-9B（见 [archive/p25_0/P25_0_MODEL_DECISION.md](archive/p25_0/P25_0_MODEL_DECISION.md)）
- Frozen compare setup（见 [archive/p25_0/P25_0_FROZEN_COMPARE_SETUP.md](archive/p25_0/P25_0_FROZEN_COMPARE_SETUP.md)）
- Case book / pairwise table / state-change compare / funnel compare / patch effectiveness compare

**结论**：基线 reward ≈ 0.59（10 样本 forensic subset）。

---

## 2. p25.1 setup — 10 样本 forensic subset

**目标**：选出 10 个可代表的样本作为后续 iteration subset。

**产出**：
- [archive/p25_1/P25_1_SETUP.md](archive/p25_1/P25_1_SETUP.md)
- [archive/p25_1/P25_1_ITERATION_SUBSET.md](archive/p25_1/P25_1_ITERATION_SUBSET.md)
- [archive/p25_1/P25_1_CASEBOOK.md](archive/p25_1/P25_1_CASEBOOK.md)
- [archive/p25_1/P25_1_PAIRWISE_TABLE.md](archive/p25_1/P25_1_PAIRWISE_TABLE.md)

**10 样本 ID**：`2Cg4YrsCMA, 9EBSEkFSje, EXGahWDp1E, IqaQZ1Jdky, NhLBhx5BVY, Ze49bGd4ON, hj323oR3rw, kdriw2a8sl, meY36sGyyv, qgyF6JVmar`

---

## 3. p25.1 progression_gate_v1 — ❌ 失败

**想法**：识别 target 是 fallback/broad/weak_conflict 时阻断 aggressive recovery。

**结果**：塌缩结果，max_turns 配置污染；全样本 reward 未改善或下降。

**详见** [FAILED_EXPERIMENTS.md § 1](FAILED_EXPERIMENTS.md#1-p251-progression_gate_v1--强-gate-误伤)

---

## 4. p25.1 forensic v2 — 深度溯源

**目标**：回答"recovery push 到底从哪里来？target 质量到底什么样？"

**产出**（均在 [archive/forensic_v2/](archive/forensic_v2/)）：
- `FORENSIC_TARGET_TIMELINE_CASEBOOK_V2.md` — 按 turn 追踪 target 演化
- `TARGET_EVOLUTION_TRACE_V2.md` — target id 变化轨迹
- `TARGET_QUALITY_AUDIT.md` — target 质量分布
- `RECOVERY_PUSH_SOURCE_AUDIT.md` — push source 溯源
- `NEXT_CUT_DIRECTION_DECISION_V2.md` — 方向决策

**关键发现**：`sticky_recovery_bias` 是非 ready 推送的主要来源（后续被 TQC 观测证实）。

---

## 5. p25.1 flaw_fix_v2 — ✅ 成功 (+0.0417)

**目标**：修三个 bug 链路。

**三项改动**：
1. `flaw_progress_override` 允许 flaw 推进 recovery（解除卡死）
2. `structured report` 缺失时的安全网
3. `section detection` 大小写/空格健壮化

**结果**：Layer 3 mean 0.5923 → 0.6340；W/T/L = 7/1/2；decision 9/10 持平。

**详见** [POSITIVE_EXPERIMENTS.md § 1](POSITIVE_EXPERIMENTS.md#1-flaw_fix_v2--00417-mean)

---

## 6. p25.1 TQC observability v1 — ✅ 成功

**目标**：不改行为，为每 turn 附加五维 target/evidence 诊断。

**五维度**：
- `tqc_target_source`: real_claim / fallback_claim / mixed / empty
- `tqc_target_width`: single / small_set / broad / empty
- `tqc_evidence_grounding`: grounded / weak / fallback_only / no_aligned
- `tqc_conflict_strength`: strong_grounded / weak / missing_only / ungrounded
- `recovery_readiness_label`: ready / needs_target_refinement / needs_evidence_grounding / fallback_bridge_only / not_ready

**Layer 3 关键发现**（10 样本 60 turns）：
- 96.7% turns 处于非 ready 状态（ready 仅 3.3%）
- **89.5% recovery push 发生在非 ready 状态**
- `sticky_recovery_bias` 15/15 全部非 ready
- 非 ready push 次数与 reward 负相关

**详见** [POSITIVE_EXPERIMENTS.md § 2](POSITIVE_EXPERIMENTS.md#2-tqc-observability-v1)

---

## 7. p25.1 Recovery Entry Decision v1 — ❌ 失败 (-0.0105)

**想法**：基于 TQC 6 的数据，当 sticky 把 action 推成 `challenge_previous_hypothesis` 但 readiness ∈ {not_ready, fallback_bridge_only} 时，defer 到 `analyze_flaws` 或 `verify_evidence`。

**结果**：Layer 3 mean 0.6251 → 0.6146；W/T/L = 0/9/1；`hj323oR3rw` 恶化 −0.105。

**回滚**：行为代码已移除；TQC 诊断字段保留。

**详见** [FAILED_EXPERIMENTS.md § 2](FAILED_EXPERIMENTS.md#2-recovery-entry-decision-v1--defer-non-ready-sticky-push)

---

## 当前主线 = p25.1 + explicit recovery phase + TQC observability + flaw_fix_v2

- Mean reward (Layer 3 10 样本): **0.6251**
- Decision correct: **9/10**
- 最新 commit: `e1f8f1e`（回滚 RED v1 defer 行为）

---

## 不要再重做的方向（基于历次失败）

见 [FAILED_EXPERIMENTS.md § "Do Not Retry" 列表](FAILED_EXPERIMENTS.md#do-not-retry-列表)：

- progression_gate / throttle / gate 变体
- sticky 全局 restraint
- 任何基于 "阻断 recovery" 的简单规则
- fallback target 全局 suppress

---

## 推荐下一步方向

**Readiness Repair / Target Refinement v1** — 从"阻止 recovery"转向"当 target 不 ready 时主动建设"。详见 `POSITIVE_EXPERIMENTS.md` 末尾 recommendation section。
