# hj323oR3rw — Case Forensic

**对象**：Layer 3 10 样本中唯一 `decision_correct=0` 的样本。
**动机**：在决定下一步方向前，深挖这个 case 找出是 bug / prompt / 任务上限。

---

## 0. 事实摘要

| 项 | 值 |
|---|---|
| paper_id | `hj323oR3rw` |
| 主题 | Multimodal Open-set Test-time Adaptation (MM-OSTTA) |
| Gold decision | **Accept** (rating 6,6,6 from 3 reviewers) |
| 系统预测 | **Reject** |
| Reward | 0.3275 |
| 问题最集中在 | `decision` (0.0) + `rating_align` (0.0) |

---

## 1. Turn-by-turn 轨迹

| Turn | Action | Target | Readiness | Policy source | Patch outcome |
|---|---|---|---|---|---|
| T1 | extract_claims | [] | not_ready | manager_model | — |
| T2 | verify_evidence | [claim-1] | not_ready | evidence_progress_override | — |
| T3 | analyze_flaws | [claim-1] | needs_evidence_grounding | s4_evidence_to_flaw_override | — |
| T4 | challenge_previous_hypothesis | [claim-1] | needs_evidence_grounding | sticky_recovery_bias | `BLOCKED_BY_POLICY` |
| T5 | challenge_previous_hypothesis | **[]** | **not_ready** | sticky_recovery_bias | `EMISSION_NOT_REQUESTED` + `BLOCKED_BY_POLICY` |
| T6-T8 | 同 T5（4 个空 target 的 sticky 循环） | [] | not_ready | sticky_recovery_bias | `OUTPUT_SCHEMA_MISSING` + `BLOCKED_BY_POLICY` |

**关键观察**：T5-T8 共 4 个 turn 在 target=[] 的 sticky 循环里空转，没有显式 `finalize`，系统耗尽 max_turns=8 被迫结束。

---

## 2. Final State 关键对象

### claim-1
- status: **unsupported**
- 但 `evidence_map` 中：
  - evidence-1: weak, supports（被降级过 strong → weak）
  - **evidence-2: strong, supports**
  - **evidence-3: strong, supports**
  - evidence-4: missing, missing

即有 **2 个 strong supports**，但 claim 却被标记为 unsupported。

### flaw_candidates（都 `status=candidate`，未 confirmed）
- flaw-1 (major): "Lack of Methodological Grounding for Core Claims"
- flaw-2 (major): "Insufficient Evidence for Multimodal Fusion Strategy"

### evidence_gaps
- `"Claim claim-1 lacks grounded supporting evidence."` ← 尽管有 2 strong supports

### conflict_notes
- `"Prior judgment that claim-1 was 'supported' based on abstract presence is now in tension with the lack of methodological evidence..."`

### `_latest_patch_log.recovery_failure_message`
- `"Insufficient evidence in the provided excerpt to substantiate the core technical claims regarding the 'Adaptive Entropy-aware Optimization' and multimodal fusion strategy."`

---

## 3. Bug 定位

### Bug A（根本）— "Recovery-Failure Echo Into Critique Weakness"

系统把**自己 recovery_patch 失败产生的投诉**当成 **paper weakness** 写入 final report：

| 源头（系统投诉） | 伪装成的 paper weakness |
|---|---|
| `recovery_failure_message` | "Insufficient evidence in provided excerpt..." |
| 对应 flaw-1 | "Lack of Methodological Grounding..." |
| 对应 flaw-2 | "Insufficient Evidence for Multimodal Fusion..." |
| 对应 evidence_gaps | "Claim claim-1 lacks grounded supporting evidence" |

**"Insufficient evidence in provided excerpt"** 原本是说"系统拿到的摘录里没包含方程"，不是"论文没有方程"。但它被 **worker agent 翻译成了"paper has major flaw"**。

### Bug B（直接触发 reject）— `infer_final_decision` 把 `candidate` 当 `confirmed` 算

代码位置 `state.py:1740-1765`：

```python
major_flaws = sum(
    1 for flaw in state.get("flaw_candidates", [])
    if flaw.get("severity") == "major" 
    and flaw.get("status") not in {"downgraded", "retracted"}
)
...
if critical_flaws > 0 or major_flaws >= 2 or unresolved >= 6 or conflicts >= 4:
    return "reject"
```

对 `hj323oR3rw`: `major_flaws = 2`（都是 `candidate` 状态，从未 confirm）→ 触发 `major_flaws >= 2` → auto-reject。

Candidate = 未验证的"怀疑"，Confirmed = 已验证。当前规则把两者同权，让未经确认的怀疑也能触发 auto-reject。

### Bug C（系统级）— 系统几乎从不输出 accept

跑历史 20 个实验文件统计：

| 实验数 | 总样本 | accept 预测 |
|---|---|---|
| 21 | ~160 | **4** (2.5%) |

系统结构性偏 reject。`infer_final_decision` 的 accept 分支过严：`major == 0 AND strong_support >= 2 AND unresolved <= 3`，几乎不可能满足。

### Bug D（metric 假象）— 9/10 correct 是数据偏态而非模型能力

- forensic subset: 9 reject / 1 accept → 总是猜 reject 得 9/10 = 90%
- 完整 test.parquet: 30 reject / 9 accept → 总是猜 reject 得 30/39 = 77%

当前系统 "**9/10 decision_correct**" 实际上是"always-predict-reject + 数据集偏 reject" 的合谋，不是 decision 能力。

---

## 4. Bug A 的诊断为何重要

Bug A 不在单个函数里，在**整个 recovery_patch → flaw → final_report 管线**：

1. excerpt 不全 → worker agent 验证失败
2. `recovery_failure_message` 被生成，内容是关于 excerpt 的局限
3. 这些信息被 **critique agent / flaw creator 再吸收**，变成 flaw_candidates 的 description
4. flaw_candidates 被 `_render_weaknesses` 直接写入 final report
5. `infer_final_decision` 看到 major_flaws ≥ 2 → reject

**系统没区分"我们没看到"和"论文没有"**。

---

## 5. 对比：meY36sGyyv (gold=reject, dec_c=1)

两个样本 state features 几乎一样：

| 特征 | hj323oR3rw (gold=accept) | meY36sGyyv (gold=reject) |
|---|---|---|
| strong_support | 2 | 3 |
| major candidate | 2 | 1 |
| conflicts | 1 | 1 |
| unresolved | 5 | 5 |
| confirmed flaws | 0 | 0 |

两个样本在 `review_state` 层面**几乎不可区分**，却有相反的 gold 判断。

**结论**：任何基于现有 state count 的 threshold tweak，都会把 hj323oR3rw 往 accept 改时同时把 meY36sGyyv 错误地往 accept 改（或反之）。**state 表达力不足以线性分离这两个样本**。

---

## 6. 三种可能的修复（含可行性判断）

### 路径 A — 只修 Bug B（低风险小修复，不够）

```python
# 只把 confirmed major 计入 reject 权重
major_confirmed = sum(
    1 for f in state.get("flaw_candidates", [])
    if f.get("severity") == "major" and f.get("status") == "confirmed"
)
```

**问题**：因为系统**从不 confirm flaws**（确认流程走不通），所有样本都会变 major=0。然后 accept 分支也不会过（`unresolved <= 3` 严）。结果 hj323oR3rw 仍然 reject。

### 路径 B — 改 prompt 让 manager 显式输出 `final_decision`（中风险中收益）

当前 manager 从不输出 `final_decision`，`infer_final_decision` 总是走 fallback 机械规则。让 manager 在最后一轮 prompt 里明确输出 accept/reject 判断。

**风险**：如果 model 也倾向 reject（基于错误的 critique），改 prompt 不能自动治愈 Bug A 的污染链。需要配合 Bug A 的清理。

### 路径 C — 清理 Bug A 管线（高工程量高风险）

三选一或组合：
1. 过滤 `recovery_failure_message` 文本（不进入 flaw_candidates）
2. 过滤 flaw_candidates 的描述中匹配 "insufficient evidence in provided excerpt / lack of ... in provided excerpt" 的条目
3. 在 `_render_weaknesses` 阶段做语义白名单（只保留 confirmed flaws 或 grounded_evidence 支持的 flaws）

**风险**：heuristic 过滤容易误伤；可能类似 progression_gate 的老路。

### 路径 D — 停手写论文（低风险零收益）

承认 state representation 上限；把 Bug A / B / C / D 写进论文 "limitations and failure modes" 章节。当前主线 0.6251 已是可展示的数字。

---

## 7. 我的判断

1. **Bug A 是真 bug，但修复路径不 minimal**。不属于 flaw_fix_v2 那种一行 bug fix。
2. **Bug B 可以局部修**，但单独修不会让 hj323oR3rw 变 accept（`unresolved <= 3` 这条也得放宽，而一放宽就会影响其它 gold=reject 样本）。
3. **Bug D 是最 honest 的发现**：当前 "9/10 decision correct" 是假象。任何诚实的 evaluation 需要在完整 test set（30/9 reject/accept）上跑。
4. **state 表达力上限**：hj323oR3rw 和 meY36sGyyv 状态特征重合，说明当前 review_state schema 无法区分它们。更深的 fix 需要改 state 结构 —— 这和重整 architecture 同级。

---

## 8. 建议

优先级：

1. **跑一次完整 test (39 样本) 验证 decision_correct 真相**（低成本，一次 inference）
   - 若仍然 30/39，说明系统 just predicts reject，当前指标不可信
   - 若更低（<30/39），说明其它样本也有 regression

2. **Bug B 最小 patch + 完整 test 验证**（中成本）
   - 把 `candidate` 与 `confirmed` 权重分离
   - 在完整 test 上对比是否改善 accept 覆盖率

3. **如果 1/2 都不改善，停手写论文**（零成本）
   - 把 Bug A-D 汇总写进 limitations
   - 不再追 10 样本小 reward 改进

4. **不推荐**（基于之前失败的经验）：
   - 任何新 controller
   - 任何基于 flaw description 字符串匹配的启发式过滤
   - 任何扩大 sticky / 改 recovery gating 的方向

---

## 9. 如果继续做，推荐 Bug B 最小修复 + 完整 test 验证

```python
# state.py:1740 改 infer_final_decision
def infer_final_decision(state, manager_payload):
    explicit = _normalize_choice(manager_payload.get("final_decision"), FINAL_DECISIONS, "undecided")
    if explicit != "undecided":
        return explicit

    flaws = state.get("flaw_candidates", [])
    # CHANGED: only confirmed flaws count full weight; candidates count half
    critical_conf = sum(1 for f in flaws if f.get("severity")=="critical" and f.get("status")=="confirmed")
    major_conf    = sum(1 for f in flaws if f.get("severity")=="major"    and f.get("status")=="confirmed")
    critical_cand = sum(1 for f in flaws if f.get("severity")=="critical" and f.get("status")=="candidate")
    major_cand    = sum(1 for f in flaws if f.get("severity")=="major"    and f.get("status")=="candidate")

    strong_support = sum(
        1 for e in state.get("evidence_map", [])
        if e.get("strength")=="strong" and e.get("stance") in {"supports","partially_supports"}
    )
    unresolved = len(_open_unresolved_questions(state))
    conflicts = len(state.get("conflict_notes", []))

    # Confirmed issues trump support
    if critical_conf > 0 or major_conf >= 2:
        return "reject"

    # Strong unconfirmed red flags
    if critical_cand >= 1 or major_cand >= 3 or unresolved >= 6 or conflicts >= 4:
        return "reject"

    # Accept if grounded support and bounded candidate flaws
    if strong_support >= 2 and major_cand <= 2 and unresolved < 6:
        return "accept"

    return "reject"
```

**预期效果**（用当前 Layer 3 state 模拟）：

| paper_id | gold | current pred | proposed pred |
|---|---|---|---|
| hj323oR3rw | accept | reject | **accept** ✓ |
| meY36sGyyv | reject | reject | **accept** ✗（破坏） |
| 其它 8 | reject | reject | reject（保持） |

不幸：**meY36sGyyv 会被 break**，因为它的特征和 hj323oR3rw 太接近。10 样本 W/T/L = 1 / 8 / 1 = **净零收益**。

所以即使是这个看起来合理的修复，在 forensic subset 上净零。**这恰好支持了"state 表达力上限"的诊断**。

---

## 10. 最终结论

**Bug A/B/C 真实存在**，但在 10 样本 forensic subset 上无法通过局部修复获得净收益。

**真正有意义的下一步是跑 39 样本完整 test**：
- 让我们用更大 sample 量看 Bug B 修复的真实分布影响
- 同时让我们看 "always-predict-reject" 的真实上限究竟是多少

这是一个**低成本、结果可解读、不需要改代码行为**的验证，满足 memory 里"single controller + net positive required" 原则。
