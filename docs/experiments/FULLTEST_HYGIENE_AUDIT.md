# Full-test Decision Bias + State Hygiene Audit

**日期**：2026-04-24
**依据**：`EVALUATION_METRICS_CHARTER.md` 第五节统一评估表
**数据源**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`（39 样本）
**脚本**：`scripts/audit_fulltest_hygiene.py`

**审计目的**：
1. 系统是否结构性 always-reject
2. final report 是否存在 meta leakage
3. claim status 是否和 evidence 一致
4. candidate flaw 是否被当 confirmed flaw 使用
5. 是否有恢复 accept 能力的离线规则空间

---

## A. Decision Health — **结构性 always-reject 已确认**

| 指标 | 值 |
|---|---|
| Samples | 39 |
| Gold 分布 | {reject: 30, accept: 9} |
| 预测分布 | **{reject: 39}** |
| accuracy | 0.7692 |
| always-reject baseline | 0.7692 |
| **gain over baseline** | **+0.0000** |
| accept precision | 0.0000 |
| accept recall | **0.0000** |
| accept F1 | 0.0000 |
| reject F1 | 0.8696 |
| **macro-F1** | **0.4348** |

**Confusion matrix**：

| | pred=accept | pred=reject |
|---|---|---|
| gold=accept | 0 | **9** |
| gold=reject | 0 | 30 |

**结论**：Decision 层**完全等同于 always-reject baseline**。这不是系统判断能力，只是数据分布的投影。

---

## B. State Hygiene — **广泛存在状态污染**

| 指标 | 总计 | 受影响样本 |
|---|---|---|
| `unsupported_with_strong_support` | **20** | **38.5% (15/39)** |
| `unsupported_with_2plus_strong` | 4 | 10.3% (4/39) |
| `supported_with_strong_contradiction` | 0 | 0.0% (0/39) |
| **`stale_evidence_gap`** | **31** | **53.8% (21/39)** |
| `candidate_major_used_for_reject` | 6 | 15.4% (6/39) |
| `recovery_failure_echo_flaws` | 1 | 2.6% (1/39) |
| `meta_in_evidence_gaps` | 0 | 0.0% (0/39) |
| `system_meta_phrase_in_final_weakness` | 1 | 2.6% (1/39) |
| **`excerpt_limitation_as_weakness_flaw`** | **4** | **10.3% (4/39)** |

### 重要解读

1. **`unsupported_with_strong_support = 20 / 38.5% 样本**：系统有 20 对 (claim, evidence) 组合里，claim 明明有 ≥1 strong support 但状态却被锁成 unsupported。`hj323oR3rw` 是其中最严重的（2 个 strong supports 仍被标 unsupported）。这是 **claim-evidence consistency 破坏** 的广泛证据。

2. **`stale_evidence_gap = 31 / 53.8% 样本**：超过一半样本有"evidence_gap 文本说 claim X lacks evidence 但 claim X 已有 strong support"的情况。这是 **stale state 不清理** 的系统性问题。

3. **`candidate_major_used_for_reject = 6 samples**：6 个样本的 reject 决策直接由 ≥2 个 candidate major flaws 触发，0 confirmed。这 6 个样本的 reject 判断**没有被确认的 flaw 支撑**。

4. **`excerpt_limitation_as_weakness_flaw = 4 samples**：4 个样本的 flaw description 里明确含有 "provided excerpt"，**是系统上下文不足的直接抱怨**，不应作为论文 weakness。

5. meta leakage 在 final report 里相对少（仅 1 样本），但在 flaw_candidates 里更多（4 样本 excerpt 关键词 + 1 样本 recovery pattern）。

---

## C. Evidence / Flaw Grounding — **只有 3.8% flaw 被 confirm**

| 指标 | 总计 | 占比 |
|---|---|---|
| `grounded_weakness` (有 evidence_id 且非 meta) | 28 | 53.8% |
| `ungrounded_weakness` (无 evidence 或是 meta) | 24 | 46.2% |
| `fallback_generated_flaw` | 0 | 0.0% |
| **`confirmed_flaw`** | **2** | **3.8%** |
| **`candidate_flaw`** | **50** | **96.2%** |
| `downgraded_flaw` | 0 | 0.0% |
| `retracted_flaw` | 0 | 0.0% |
| `meta_flaw` | 1 | 1.9% |

**总 flaws = 52**，**grounded rate = 53.8%**

### 重要解读

1. **96.2% flaws 停在 candidate 状态**：flaw 生命周期管理几乎没工作。整个系统只有 **2 次**把 candidate 升级为 confirmed。这是 **flaw validation 机制失效** 的核心证据。

2. **Grounded rate 53.8%**：只有一半 flaw 有合法的 evidence 关联。另一半（24 个）或者无 evidence_id，或者描述是 meta。

3. **无 downgraded / retracted**：0 次系统主动否定 / 撤回 flaw。recovery_patch 几乎从不在 flaw 生命周期上产生抑制效果。

---

## D. Recovery Effectiveness

| 指标 | 值 |
|---|---|
| total turns | 280 |
| `recovery_attempt_count` | 119 |
| `recovery_emitted_count` | 70 |
| `recovery_validated_count` | 113 |
| `recovery_committed_count` | 20 |
| `recovery_push_triggered` | 119 |
| **`recovery_commit_rate`** | **16.8%** |
| `blocked_by_policy_count` | **79** (66% of attempts) |
| `no_effect_patch_count` | 20 |

**注**："no effect" 指 committed 但 turn_log 的 `new_items` 和 `revision_events` 都为空；实际 commit 对 claim status 有影响（见 `RECOVERY_EFFECTIVENESS_ANALYSIS.md` E 节的 90% 降级数据）。

### 重要解读

- **2/3 attempt 被 BLOCKED_BY_POLICY 拦截**
- **commit_rate 仅 16.8%**
- Recovery 对 state 的"可见变化"集中在 status 降级，不在新增实体

---

## E. Target Quality — **41% push 发生在 empty_target**

| target_quality_label | turns | % | recovery_pushes | push rate |
|---|---|---|---|---|
| `narrow_real_target` | 105 | 37.5% | 45 | 42.9% |
| **`empty_target`** | **90** | **32.1%** | **49** | **54.4%** |
| `broad_target` | 49 | 17.5% | 13 | 26.5% |
| `fallback_target` | 24 | 8.6% | 0 | 0.0% |
| `weak_target` | 12 | 4.3% | 12 | **100.0%** |

**target_drift_events** (相邻 turn target 互不包含): **0**

### 重要解读

1. **32% turn 发生在 `empty_target` 状态 + 54.4% 的 empty_target turn 仍被推 recovery**：**49 次 recovery push 对空目标硬推**，占总 push 的 **41%**。这是系统 sticky_recovery_bias 在 hj323oR3rw 里看到的"empty-target 4-turn 循环"模式的放大投影。

2. **`weak_target` 100% 被推 recovery**：12 / 12，尽管 weak 的定义就是"目标不可靠"。这也是系统忽略 TQC 信号的证据。

3. **`fallback_target` 0 push**：fallback 充当了"观察 bridge"而非"recovery target"——这是好的行为。

4. **`narrow_real_target` 42.9% push rate**：1/3 以上 narrow target 也被推 recovery。narrow target 下的 push 是**合理可期待的**（见 Recovery 分析中 needs_target_refinement 38.5% commit 率）。

5. **`target_drift = 0`**：turn 间 target 没有"互不包含"的跳变——但这掩盖了"empty → non-empty → empty"的震荡模式（hj323oR3rw 里就是 T4: [claim-1] → T5-T8: []）。

---

## 附录：Meta-leak 样本案例

| paper_id | gold | pred | meta_flaws | meta_weak | total |
|---|---|---|---|---|---|
| hj323oR3rw | Accept | reject | 1 | 1 | **2** |

目前只有 `hj323oR3rw` 一个样本在 flaw 和 final report 都触发 meta 匹配。其它 3 个 `excerpt_limitation_as_weakness_flaw` 样本虽然 flaw 含 "provided excerpt"，但没被 regex 完整匹配（因为描述里未出现"insufficient evidence in provided excerpt"的标准组合）。这意味着 meta 泄漏是**分布式**的，不只是一条模式，后续需要更宽的匹配库。

---

## 综合诊断

从 Charter 第四节"有效改动的 7 条标准"反向对照当前 mainline：

| 标准 | 当前值 | 状态 |
|---|---|---|
| 1. state inconsistency 减少 | unsup_strong=20 (38% samples), stale_gap=31 (54% samples) | ❌ 广泛污染 |
| 2. meta leakage 减少 | meta_flaws=1, excerpt_flaws=4, meta_weak=1 | ⚠ 存在但有限 |
| 3. grounded weakness 比例 | 53.8% | ⚠ 中等 |
| 4. recovery commit 稳健 | commit_rate=16.8%, no_effect=20 | ❌ 低 |
| 5. accept recall 不为 0 | **0.0** | ❌ |
| 6. macro-F1 高于 baseline | 0.4348 (=baseline) | ❌ 无增益 |
| 7. final report 少 meta 写入 | 1 样本 | ✓ 相对干净 |

**7 条里 4 条 ❌, 1 条 ⚠, 1 条 ✓**。

---

## 可行的 Offline 规则探索（回答审计目的 #5）

基于当前数据，能否通过离线后处理让 accept 召回非零？

### 候选规则 1：`unsupported_with_strong_support` 反推 accept

对每个样本，若存在 claim 满足：
- status == `unsupported`
- 有 ≥ 2 strong supports
- 无 strong contradiction
- 样本 critical_confirmed_flaw == 0

则"将该 claim 视为 supported"重新走 `infer_final_decision`。

**预期影响**：4 个 sample 有 `unsup_2plus_strong` → 将这些 claim 视为 supported 重推。需要跑一次 simulate 验证。

### 候选规则 2：剔除 excerpt 语义的 flaw

所有 flaw description 含 "provided excerpt" / "insufficient evidence in excerpt" 的，在 decision 时**不计 severity**。

**预期影响**：4 个 `excerpt_limitation_as_weakness_flaw` 样本受影响，其中若 candidate_major 数量降到 < 2 则可能翻 accept。

### 候选规则 3：confirmed-only flaws for decision

只有 confirmed flaw 计入 `infer_final_decision` 的 major_flaw 阈值。

**已知失败**：在 full test 上 Bug B 模拟（见 `FULLTEST_VS_SUBSET_COMPARISON.md` 第 5 节）结果是 +1 correct, -3 错误 = -2 净效果。

### 候选规则 4：hygiene-conditioned accept

若样本同时满足：
- strong_support_count >= 2
- unsupported_with_strong_support > 0 (即系统自己的 status 污染了)
- candidate_major <= 2
- confirmed_major == 0

则翻 accept。

**预期**：在 hj323oR3rw 上生效（有 2 strong supports + unsup_strong=1+ + candidate_major=2）。需验证是否误伤其它 reject 样本。

---

## 建议的下一步

依然遵循 Charter 第四节"真正有效的改动必须满足 7 条"，任何 offline 规则必须：

1. **至少保持 macro-F1 ≥ 0.4348**（不倒退）
2. **accept recall > 0**
3. **不增加 meta leakage**
4. **不降低 grounded flaw rate**

具体优先级：

### 建议 1 (低成本/纯代码)：实现候选规则 4 的 offline simulator
不改 inference, 只读 jsonl 后重走 decision 规则。测试在 39 样本上 macro-F1 与 accept recall 如何变化。

### 建议 2 (中成本/新跑 inference)：修 claim-evidence 同步环节
`unsupported_with_strong_support = 20` 是 hygiene 最严重的问题。修这个不需要改 prompt, 只需要在 `_reconcile_claim_status` 或等效的 consistency check 里加一条规则："有 ≥2 strong supports 且无 strong contradicts 时，status 至少为 partially_supported"。

**注意**: 这是改代码, 需要在 subset 上先 smoke, 再跑 full test 验证。2-3h。

### 建议 3 (写作为主)：把 Audit 结果写入论文 evidence section
本审计报告的 A-E 五类指标正是 Charter 推荐的 "State Hygiene Audit" 报告格式。可直接作为论文实验章节的 baseline hygiene profile。

### 不建议

- 任何追求 decision accuracy 的 threshold tweak（违反 Charter 四-2）
- 任何减少 recovery push 的 gate（违反 Charter 四-3，且已经失败过）
- 新 controller（违反 memory "do not pursue new sticky / gate / throttle"）

---

## Artifacts

- **本审计脚本**：`scripts/audit_fulltest_hygiene.py`
- **本审计数据**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`
- **Charter**：`EVALUATION_METRICS_CHARTER.md`
- **相关文档**：
  - `docs/experiments/FULLTEST_VS_SUBSET_COMPARISON.md`
  - `docs/experiments/RECOVERY_EFFECTIVENESS_ANALYSIS.md`
  - `docs/experiments/HJ323_CASEBOOK.md`
