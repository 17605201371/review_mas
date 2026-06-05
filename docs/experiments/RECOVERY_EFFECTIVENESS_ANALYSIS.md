# Recovery Push Effectiveness Analysis — Full 39-Sample Test

**日期**：2026-04-24
**视角**：Error recovery + evidence alignment（不是 decision accuracy）
**数据源**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`（39 样本，280 turns，119 push events）

**核心问题**：当 recovery_push 触发时，系统**真的在修 error 吗**？

---

## 0. 数据体量

| 指标 | 值 |
|---|---|
| 样本数 | 39 |
| 总 turn 数 | 280 |
| recovery_push_triggered 事件 | **119** |
| Push 触发率 | **42.5%** 的 turn |

每 2.35 个 turn 就有一次 push。这是很高频的行为。

---

## 1. Push 执行结果分布（A）

| 结果 | 数量 | 占比 |
|---|---|---|
| committed（真正 commit 成功） | **20 / 119** | **16.8%** |
| validated 未 committed | ~20 | ~17% |
| emitted 未 validated | ~30 | ~25% |
| attempted 未 emitted | ~45 | ~38% |
| 未 attempted | 剩余 | — |

**Push 的 commit 成功率只有 17%**。大多数 push 在 emit / validate / commit 三个阶段之一被拦截。

---

## 2. Push 按 TQC readiness 分桶（B）—— **最重要的观察**

| readiness | pushes | committed | commit % | status_chg % | new_items mean | revision_events mean |
|---|---|---|---|---|---|---|
| `ready_for_aggressive_recovery` | 2 | 0 | **0.0%** | 50.0% | 0.00 | 0.00 |
| `needs_target_refinement` | 13 | 5 | **38.5%** | **76.9%** | 0.00 | 0.00 |
| `needs_evidence_grounding` | 54 | 15 | **27.8%** | 48.1% | 0.11 | 0.70 |
| `fallback_bridge_only` | 0 | — | — | — | — | — |
| `not_ready_for_recovery` | 50 | **0** | **0.0%** | 10.0% | 0.04 | 0.20 |

### 关键发现

1. **`not_ready_for_recovery` 下 50 次 push 零 commit** —— 42% 的 push 是"徒劳"（TQC 已经标红但系统硬推）
2. **`needs_target_refinement` 下 commit 率最高（38.5%）+ status_chg 率最高（77%）** —— 这是 recovery 最能发挥作用的 readiness
3. **`ready_for_aggressive_recovery` n=2, commit=0** —— 样本太少，但表明"最绿灯"状态不一定带来 commit
4. **TQC 信号确实预测到了 recovery 的有效性梯度**（not_ready 0% ≪ needs_refinement 38.5%）

### 解读

TQC 作为 **observability 层** 是**有效的诊断信号**：
- 它能区分"什么时候 recovery 能起作用"
- 它能识别"什么时候 recovery 是徒劳"

但系统的 push policy（主要是 `sticky_recovery_bias`）**并没有用这个信号**，导致 42% push 发生在 not_ready 状态下，全部失败。

这是**TQC 观察层的价值**：即使 v1 实验里 TQC-gated defer 没提升 reward，**TQC 揭示的 readiness ≠ push 的决策原则** 这件事本身就是论文价值。

---

## 3. Push 按 source 分桶（C）

| push_source | pushes | committed | commit % | status_chg % | new_items mean | conflicts_resolved |
|---|---|---|---|---|---|---|
| `sticky_recovery_bias` | **99** | 20 | **20.2%** | 40.4% | 0.00 | 0 |
| `manager_model` | 18 | 0 | **0.0%** | 5.6% | **0.44** | 0 |
| `evidence_progress_override` | 2 | 0 | 0.0% | 50.0% | 0.00 | 0 |

### 关键观察

- **sticky_recovery_bias 是 83% 的 push 来源**，commit 率 20%
- **`manager_model` 自己出的 push 从不 commit** —— 18 次 push, 0 commit, 但 new_items mean = 0.44。这说明 manager 自己要求 recovery 时，recovery 模式没进入或失败，但 **new_items 还在产生**（走的不是 recovery_patch 路径）
- `evidence_progress_override` 只有 2 次

### 解读

**主动触发的 sticky recovery > 模型自身要求的 recovery**。这反常但有物理意义：
- sticky 是在系统检测到"卡住模式"后强制介入，目标明确（claim/flaw id）
- manager_model 要求 recovery 时，目标模糊，recovery_patch 没法处理

---

## 4. State delta magnitude（D）—— **Recovery 的贫瘠**

每次 push 产生的 state 变化：

| 字段 | mean | median | max | 非零比例 |
|---|---|---|---|---|
| `new_items_count` | 0.07 | 0 | 2 | **7 / 119 = 5.9%** |
| `retracted_items_count` | 0.00 | 0 | 0 | **0 / 119 = 0%** |
| `downgraded_items_count` | 0.01 | 0 | 1 | 1 / 119 = 0.8% |
| `revision_events_count` | 0.40 | 0 | 9 | **10 / 119 = 8.4%** |
| `revised_entity_count` | 0.40 | 0 | 9 | 10 / 119 = 8.4% |
| `resolved_conflict_count` | **0.00** | 0 | 0 | **0 / 119 = 0%** |

### 关键发现

- **119 次 push 里**：
  - 只有 **5.9%** 产生了新实体（new_items）
  - 只有 **8.4%** 产生了 revision events
  - **0 次** 产生 retraction
  - **0 次** 解决冲突
- **绝大多数 push 的 state delta 是 0**

### 解读

**Recovery 在"形式上"触发得很多，但在"实质上"几乎不产生 state 变化**。这就是 hj323oR3rw 样本中看到的"sticky 循环空推 4 次但 target=[]"模式，在整个数据集上的放大投影。

---

## 5. Target status 转变（E）—— **Recovery 的方向**

当 recovery 真的产生 status 变化时，转变分布：

| target_type | old_status | new_status | count | 解读 |
|---|---|---|---|---|
| claim | partially_supported | **unsupported** | **18** | **降级** |
| claim | supported | **unsupported** | **13** | **降级** |
| claim | uncertain | **unsupported** | **7** | **降级** |
| claim | unsupported | supported | 3 | **升级** ✓ |
| claim | (empty) | uncertain | 1 | 初始化 |

### 核心观察

- **总 status 变化 42 次**
- **降级 38 次 (90.5%)**（partially_supported / supported / uncertain → unsupported）
- **升级只有 3 次 (7.1%)**
- **从 unsupported 回到 supported** 只占 recovery 产生的 status 变化的 7%

### 解读 —— **这是 "Recovery-Failure Echo" 假设的终极证据**

系统的 recovery 主要在做**否定性判断**：
- 看到"目前的 supported claim 证据不够强" → 降级为 unsupported
- 看到"partially_supported claim 的证据被挑战" → 降级为 unsupported
- 几乎**从不**"找到新证据让 unsupported claim 变 supported"

这和 `hj323oR3rw` casebook 里看到的**完全一致**：
- 该样本的 recovery_patch 只产生 "insufficient evidence in provided excerpt" 消息
- 这被 worker 吸收变成 flaw_candidate
- flaw_candidate 把 supported claim 拉回 unsupported
- 最终 final_report 基于"unsupported claim + major flaws"→ reject

**整个数据集上这个模式是系统性的**：recovery 不是在"修 error"，而是在"否定之前的判断"。

---

## 6. 每样本 commit rate vs final alignment（F/G）

### 按 commit rate 分桶

| commit_rate_bucket | n | reward_mean | stance_mean | critique_mean |
|---|---|---|---|---|
| 0% (no commits) | **23** | 0.4704 | 0.4783 | **0.7880** |
| ≤ 50% | 15 | 0.4557 | 0.4856 | 0.8417 |
| > 50% | 1 | 0.6827 | 0.5330 | 1.0000 |

### 零 commits vs 有 commits

| 组 | n | reward | stance | critique |
|---|---|---|---|---|
| Zero commits | 23 | 0.4704 | 0.4783 | 0.7880 |
| Some commits | 16 | 0.4699 | 0.4886 | **0.8516** |
| **Delta** | — | **-0.0005** | **+0.0103** | **+0.0636** |

### 关键观察

- **reward 层面：zero commit 与 some commit 几乎一致（0.4704 vs 0.4699）**
- **stance_align 轻微提升（+0.010）**
- **critique 提升明显（+0.064）** —— 这是 recovery commit 最显著的贡献
- 但 critique 提升是否 **来自 recovery commit 本身**，还是**来自"样本本身更复杂 → 更多 recovery 触发 → 更多 critique 输出"**，需要更细的分析才能区分

### 解读

- **Recovery commit 对 reward 基本无影响**
- **Recovery 对 critique 可能有轻度正向贡献**（+0.064），但可能是相关非因果
- 样本 `kam84eEmub`（2/2 commit 率 100%）reward 0.6827 critique 1.0 — 是 outlier，不足以支撑因果结论

---

## 7. 综合诊断

Recovery 管线目前呈现 **"诊断层健康，执行层失效"** 的态势：

| 层 | 状态 | 证据 |
|---|---|---|
| **诊断层（TQC）** | ✅ 工作正常 | readiness 成功预测 commit 率梯度（0% → 38.5%） |
| **触发层（push）** | ⚠️ 过度触发 | 42% 的 turn 有 push, 42% push 在 not_ready 状态 |
| **执行层（recovery_patch）** | ❌ 大部分失败 | 17% commit 率, 92% state delta 为零 |
| **效果层（state 变化）** | ❌ 方向错误 | 90% 的 status 变化是"降级"，只有 7% 是"升级" |
| **对 reward 贡献** | ❌ 近零 | reward 与 commit rate 相关 ≈ 0 |

---

## 8. 证据层 vs 决定层的脱钩（关联 Bug C）

`BXY6fe7q31` 是极端案例：
- gold = accept
- **stance_align = 0.9455**（全测试最高之一）
- **0 recovery push**（无需 recovery，evidence 已充分）
- **但 pred = reject**（`infer_final_decision` 机械规则压制）

这支持论文的核心观点：**系统的 evidence 对齐能力强于它的 decision 判断能力**。Recovery 管线贫瘠并不意味着系统对论文的理解差——只是 recovery 这条"自我修正"路径没真正运作。

---

## 9. 论文叙事提纲

### 定位更新（相比 `FULLTEST_VS_SUBSET_COMPARISON.md`）

原：decision accuracy = always-reject baseline → 系统结构性失败。
新：**证据层（stance/critique）质量可接受，recovery 管线"忙而无效"，诊断层（TQC）已可识别 recovery 质量差异**。

### 可讲的故事

1. **TQC observability 是本工作的有效贡献**
   - 即使 TQC-gated defer 没提升 reward，TQC 信号本身正确预测了 recovery 质量梯度（0% → 38.5%）
   - 可作为 "observability before intervention" 的 motivating case study

2. **Recovery 管线的"诊断 ≠ 执行"脱钩**
   - 诊断层（TQC）知道 42% push 在 not_ready 状态
   - 但触发层（sticky）不使用 TQC 信号，继续推
   - 执行层（recovery_patch）成功率仅 17%
   - 这是 multi-agent 系统常见但罕被量化的病理

3. **Recovery-Failure Echo：recovery 产生的"insufficient evidence" 投诉被误吸收为 paper weakness**
   - hj323oR3rw 案例 + 整个数据集 90% "降级" 的 status 转变
   - 系统的"否定性 recovery"产生了 fake flaws

4. **Evidence alignment 质量是系统的真正强项**
   - critique = 0.81 (高)
   - stance_align 在 accept 样本上达 0.54
   - BXY6fe7q31 样本 stance = 0.95 但 decision 错

5. **Decision 层与 evidence 层脱钩（机械规则主导）**
   - `infer_final_decision` 基于 candidate flaws + unresolved counts
   - 完全没使用 stance_align / critique 信号
   - 这是一个 design flaw，但也**是系统 behavior 的核心观察**

---

## 10. 建议的下一步分析

按价值降序：

### 已完成 ✓
- A/B/C 维度的 push outcome 分析
- D/E 维度的 state delta 和 status 转变分析
- F/G 维度的 per-sample 对齐
- recovery 方向性（90% 降级）的量化证据

### 建议继续
1. **对比 Layer 3 subset 上 baseline / flaw_fix_v2 / tqc_v1 三份数据的 recovery commit rate 演进** —— 看 flaw_fix_v2 是否真的改善了 commit rate
2. **深挖 3 次 "unsupported → supported" 的正向 recovery 案例** —— 看 recovery 在什么条件下才对路
3. **对比 `manager_model` push 和 `sticky_recovery_bias` push 的 policy context** —— 看为什么 sticky 能 commit 20%，manager 自己要求的 0%

### 不建议
- 再做 full test inference（已有数据足够）
- 改 recovery_patch 策略（需要 9B 再验证 2-3h，且上 10-subset 实验证明 defer 无效）

---

## 11. Artifacts

- **脚本**：`scripts/analyze_recovery_effectiveness.py`
- **数据源**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`
- **相关文档**：
  - `docs/experiments/FULLTEST_VS_SUBSET_COMPARISON.md`
  - `docs/experiments/HJ323_CASEBOOK.md`
  - `RECOVERY_ENTRY_DECISION_V1_RESULT.md`
