# Positive Experiments — 成功改动汇总

所有**在 mainline 上验证有净增益或不改行为但提供诊断价值**的改动。

---

## 1. flaw_fix_v2 — +0.0417 mean

**时间**: 2026-04-23
**原文**: [archive/p25_1/P25_1_FLAW_FIX_V2_COMPARE.md](archive/p25_1/P25_1_FLAW_FIX_V2_COMPARE.md)

### 三项 bug 修复

| 项 | 问题 | 修复 |
|---|---|---|
| **flaw_progress_override** | flaw 已生成但系统卡在 `verify_evidence` 循环，无法推进到 `analyze_flaws` / recovery | 当 `flaw_candidates > 0` 且 conflict 存在时，覆盖 sticky-like 行为，允许推进 |
| **structured report safety net** | manager 最后没产出 structured final report，导致 reward 缺 section presence | 当 finalize 时若缺结构化 report，生成最小 section 骨架 |
| **section detection robustness** | reward section 解析对大小写 / 空格过于严格，误判"没有 decision section" | 放宽正则（case-insensitive, whitespace-tolerant） |

### Layer 1→2→3 验证结果

| Layer | N 样本 | Before | After | Delta |
|---|---|---|---|---|
| L1 快跑 | 3 | 0.588 | 0.628 | +0.040 |
| L2 中层 | 6 | 0.591 | 0.629 | +0.038 |
| **L3 forensic** | **10** | **0.5923** | **0.6340** | **+0.0417** |

- W / T / L = **7 / 1 / 2**
- Decision correct: 9/10 持平

### 为什么成功

不是新 controller，是**修基础管线 bug**。
`flaw_progress_override` 解除真实死循环；structured report / section detection 修 reward 解析层面的误判。

### 状态

**主线保留**。Commit: `8c19466`。

---

## 2. TQC Observability v1

**时间**: 2026-04-24
**原文**: [archive/tqc_and_red_v1/TQC_LAYER3_AUDIT.md](archive/tqc_and_red_v1/TQC_LAYER3_AUDIT.md)

### 设计

在 `review_manager_policy.py` 中 `apply_manager_policy_fallback` 末尾计算并注入 5 维诊断字段，通过 `normalize_manager_payload` 和 turn_log 传播到输出 JSONL。**零行为变更**。

### 五维度

| 维度 | 取值 |
|---|---|
| `tqc_target_source` | empty_or_unknown / fallback_claim / mixed_real_and_fallback / real_claim |
| `tqc_target_width` | empty / single_target / small_target_set / broad_target_set |
| `tqc_evidence_grounding` | no_aligned_evidence / fallback_evidence_only / weak_evidence / grounded_evidence |
| `tqc_conflict_strength` | weak_conflict / missing_evidence_only / unresolved_but_ungrounded / strong_grounded_conflict |
| `recovery_readiness_label` | not_ready_for_recovery / fallback_bridge_only / needs_target_refinement / needs_evidence_grounding / ready_for_aggressive_recovery |

### Layer 3 关键发现（10 样本 / 60 turns）

| 发现 | 数据 |
|---|---|
| turns 处于 ready 状态的比例 | **3.3%** (2/60) |
| turns 处于 not_ready 的比例 | **50%** (30/60) |
| recovery push 发生在非 ready 状态 | **89.5%** (17/19) |
| `sticky_recovery_bias` 在 ready 状态的次数 | **0/15** |
| 非 ready push 次数与 reward 相关性 | **负相关**（`hj323oR3rw` 最低 reward / 最多非 ready push） |

### 为什么成功

**观察不改行为** = 不可能恶化 reward，只会增加信息。

诊断数据本身成为重要论文材料：
- 证明系统"失败的结构性原因在 target 对象质量而非 recovery 能力"
- 为后续（已失败的）Recovery Entry Decision v1 和未来 Target Refinement 提供决策数据

### 状态

**主线保留**。Commit: `84a968c`。分析脚本: `scripts/analyze_tqc.py`。

---

## 小结

| 改动 | 类型 | 净收益 | 保留原因 |
|---|---|---|---|
| flaw_fix_v2 | bug 修复 | +0.0417 reward, 7/1/2 | 真实管线问题 |
| TQC observability v1 | 诊断层 | 0 reward, 信息增益大 | 零风险, 论文证据 |

---

## 当前主线性能

- **Mean reward (Layer 3 10 样本)**: 0.6251
- **Decision correct**: 9/10
- **Baseline 起点**: 0.5923
- **总累积增益**: +0.0328

---

## 推荐下一步方向

基于 TQC 数据和 Recovery Entry Decision v1 失败的经验，下一个正向尝试应该是：

### Readiness Repair / Target Refinement v1

从"阻止 recovery"转向"当 target 不 ready 时主动建设内容"。按 TQC label 分流：

| TQC label | 建设性动作 |
|---|---|
| `needs_target_refinement` (n=11) | 生成/选择更窄 target（主动 claim 重聚焦） |
| `needs_evidence_grounding` (n=15) | 明确 claim-evidence 对齐（主动 evidence 补采） |
| `fallback_bridge_only` (n=2) | 把 fallback bridge 到真实 claim |
| `not_ready_for_recovery` (n=30) | 进入 readiness repair 子流程 |
| `ready_for_aggressive_recovery` (n=2) | 允许 aggressive recovery |

**关键原则**：
1. 不 defer / 不 block，只做正向内容建设
2. 独立 controller，单独可测试
3. Layer 1 → 2 → 3 逐层验证；任一层 W/T/L < 3/7/0 即回滚

**风险**：工程量大，可能需要新 worker spec / prompt。比前两次（progression_gate / Recovery Entry Decision）更重。

---

## 不推荐的方向

详见 [FAILED_EXPERIMENTS.md § Do Not Retry 列表](FAILED_EXPERIMENTS.md#do-not-retry-列表)。
