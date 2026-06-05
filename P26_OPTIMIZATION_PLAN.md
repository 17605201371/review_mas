## P26 优化诊断与方案（v3 终版）

基于服务器 `codex/p26-optimization-20260524` 分支 git 历史、最近 10 个 commit、未提交 diff、smoke8 运行数据的完整分析，经两轮外部审计修正。

**审计评分演变**：v1 诊断 75% / 实施 40% → v2 诊断 85% / 安全 90% / 实施 75% → v3 修正 7 处遗留问题。

---

### Git 历史概要

当前分支从 `codex/p25-1-explicit-mainline` 演化而来。最近 commit 分三类：

**审计与文档清理**（`63f8b96`~`cb0515f`）：删除旧文档、归档实验结果、建立 V2 baseline 审计体系。不影响运行时。

**Evidence context 实验**（`be6bd1e`~`a940885`）：调整 snippet source 排序将 method 提前，但 real_strong 从 12 降到 6，**被完全 revert**。教训：source order 很敏感，不要把它和其他改动混在一起。

**当前未提交 diff**（4 文件，+362 行）：`state.py` 新增 `support_diversity_for_claims()` 和 unresolved question 自动 resolve；`review_runner.py` 新增 tokenizer-aware prompt truncation；tests 新增 96 行。

---

### 根因诊断（经审计确认）

#### P0-1：Recovery 有效修复率低

**漏斗**: 11 attempted → 5 validated → 2 committed → 2 effective repair
**Target gate**: real=2, weak=6, fallback=3

因果链：normal review 阶段未积累 verified negative evidence → recovery candidate 为空 → 目标退化为 weak/fallback → Critique 返回 blocked → salvage 失败 → terminal blocked 退出。

**观察性假象**：gate label 将 BLOCKED_BY_POLICY/INSUFFICIENT_EVIDENCE 统一标记为 `weak_target`，其中约 3 个实际是安全阻断的合理结果。

**约束**：不改 validator；不允许 quote-bank evidence 做 claim downgrade；不无条件重试 blocked patch。

#### P0-2：Method Support 被打空（empirical=9, method=1）

5 层压制链：Prompt 偏见 → Quote Bank cap=1/priority=7 → Depth 天花板（moderate）→ Promotion threshold 不对称（0.70 vs 0.60）→ Final Strong Guard。

**关键区分**：method 证明"如何实现"，empirical 证明"是否有效"，语义角色不同，不应为数量平衡拉齐门槛。先改善 retrieval，再观察 score 是否自然上升。

#### P0-3：Zero-Real 论文（kam84eEmub, WLgbjzKJkk）

kam84eEmub 有 method evidence 但被压制链卡在 medium（score=0.5263 < 0.70）。WLgbjzKJkk 反复引用同一 comparison/abstract quote（dedup 问题）。两篇需要不同修复。

#### P1-1：无 claim 获得 2+ 独立证据

8 个 group 分布在 8 个 claim 上（每 claim 1 个）。agent 复制同一 quote（`duplicate_quote_count=4`）。当前 diff 的 `support_diversity_for_claims()` 方向正确。

#### P1-2：Gap 过重（37/40 deferred targetless）

创建端问题：negative formation 和 fallback recovery 产生的 question 使用空 `related_claim_ids`。

**约束**：不做 `resolved_by_time_decay`。无法绑定的 question 转 `internal_deferred`。

#### P1-3：Negative Evidence 偏少（3 verified, 1 actionable）

"少但干净"不一定是 bug。

**约束**：不增加常态触发频率；中性词不能单独触发；regex 只生成 candidate，semantic verifier 决定 final type。

---

### 优化方案（v3 终版）

#### 实施顺序

```
T0  隔离 tokenizer-aware truncation，单独验证
R6  Dashboard 观测增强
R4a unresolved question 创建端结构化
R4b targetless question 保守回填 / internal_deferred
R3  independent evidence diversification
R1a method quota 1→2
R1b method claim / section anchor 识别
R1c method prompt 指导
R2  recovery target hydration
R5  negative precision
```

每次只改一个可解释因素。

---

#### T0: Tokenizer-Aware Prompt Truncation 隔离验证

当前未提交 diff 中 `review_runner.py` 已新增 `_truncate_prompt_for_context()`、`_prompt_token_ids()`、`_decode_prompt_tokens()` 等方法，重写了 `_format_prompt()` 逻辑。这会直接影响 agent 实际看到的 snippet 内容。

**必须在其他实验之前单独验证**：
- 记录每个 source bucket 被保留的字符/token 数
- 记录被截断的 source 类型
- 确认 method/results/table/figure 的保留率
- 如果 truncation 导致 method snippet 被截掉，后续 R1 的 quota 改善会被掩盖

**验证方式**：在 review_runner 中增加 truncation 日志（每个 agent 调用记录 prompt_token_count、truncated_source_buckets、truncated_chars），先跑一次 baseline smoke 观察 truncation 行为，再决定是否保留或调整。

**如果 truncation 行为合理**（不截断关键 source），保留并与后续实验叠加。
**如果 truncation 截掉了 method/table**，需要在 R1 之前修复 truncation budget 分配。

---

#### R6: Dashboard 观测增强

**文件**：`scripts/dashboard_run_comparison_v1.py`

新增指标：
- `recovery_effective_repair_rate = recovery_effective_repair / max(recovery_attempted, 1)`
- `recovery_validation_rate = validated / max(attempted, 1)`
- `recovery_commit_rate = committed / max(validated, 1)`
- `recovery_real_target_rate = real_target / max(attempted, 1)`
- `recovery_safe_blocked_count`：区分 safe_blocked 和真正 weak target
- `method_real_strong_support_count` 和 `method_support_ratio`（观察指标，不作为优化目标）
- `targetless_unresolved_deferred_rate = targetless_deferred / max(unresolved_deferred, 1)`（WARN 指标，非硬 FAIL）

Gate label 修正（配合 state.py）：
- 新增 `safe_blocked` gate label 值
- 当 `validated=True, commit_allowed=False, failure_code in {BLOCKED_BY_POLICY, INSUFFICIENT_EVIDENCE}` 时标记为 `safe_blocked` 而非 `weak_target`

**`safe_blocked` runtime 影响评估**（已确认）：
- gate_label 在 `_build_recovery_hydration_view()`（state.py:6918-6921）用于 contamination target 排序优先级。`safe_blocked` 分配 priority=4（排在 `empty_target=3` 之后），这是合理的降级——安全阻断的目标不应被优先选为 recovery target
- gate_label 在 `_build_recovery_patch_log()`（state.py:5498）用于 `recovery_target_commit_allowed` 判断，条件硬编码为 `== "real_target"`，`safe_blocked` 不会误触发
- Dashboard 和 audit 脚本中硬编码的 4 个 label（real/weak/fallback/empty）需要扩展为 5 个

**结论**：`safe_blocked` 对 runtime 的影响仅为排序降级（合理），可以在 R6 低风险阶段实施，但需要给 priority dict 添加 `"safe_blocked": 4`。

---

#### R4a: Unresolved Question 创建端结构化

**文件**：`agent_system/inference/review_runner.py`

所有创建 unresolved question 的位置（约 1698, 2650, 2658, 2676, 2715, 2766, 2799, 2815 等行）：将 bare string 改为结构化 dict，始终包含：

```python
{
    "question": "<question text>",
    "related_claim_ids": [<当前处理的 claim_id>],
    "related_evidence_ids": [],
    "related_flaw_ids": [],
    "created_turn": <turn_id>,
    "creation_reason": "<reason string>",
    "provenance_action": "<action_type>",
}
```

**不要**因为"当前正在处理 claim-1"就把所有 question 都绑到 claim-1。绑定规则：
- 如果 question 是由某个特定 claim 的处理过程产生的（如 evidence fallback for claim-X），`related_claim_ids = ["claim-X"]`
- 如果 question 是由全局状态产生的（如 negative evidence formation 整体），`related_claim_ids = [<当前 turn 的所有 target claim_ids>]`
- 如果确实无法确定关联，`related_claim_ids = []`，后续由 R4b 保守回填

---

#### R4b: Targetless Question 保守回填

**文件**：`agent_system/environments/env_package/review/state.py`

`_refresh_state_consistency()` 新增保守回填逻辑：
- 对 targetless 且 status=="open" 的 unresolved question：
  1. 如果 question text 明确包含 claim_id 模式（如 "claim-1"），绑定 `related_claim_ids`
  2. 如果 `creation_reason` 或 `provenance_action` 唯一指向某个 claim，绑定
  3. 否则不绑定，留给 `build_decision_hygiene_view()` 处理

`build_decision_hygiene_view()` 修改：
- 对仍无法绑定的 targetless deferred question，标记为 `internal_deferred`（不是 `resolved_by_time_decay`）
- 保留 `internal_deferred` question 在 audit trace 中可见，但在 decision hygiene 统计中不计入 `targetless_uncertainty`

当前 diff 中已有的自动 resolve 逻辑（question 的 related_claim_ids 中任一 claim 已有 real strong support → resolved）保留，它处理的是有锚点的 question。

---

#### R3: Independent Evidence Diversification

**文件**：`agent_system/environments/env_package/review/state.py`

保留当前 diff 中已有的：
- `support_diversity_for_claims()` 函数
- `quote_ids_to_avoid_by_claim` 和 quote bank 排序
- `independent_support_needs` 在 Evidence Agent observation 中传递

修正 duplicate 处理：
- `_merge_evidence()` 中当新 evidence item 的 `quote_id` 和 `claim_id` 与已有 item 完全匹配时：
  - 标记为 `duplicate_superseded`
  - 添加 `superseded_by` / `duplicate_of` 字段指向已有 item
  - **保留**在 audit trace 中（不删除原始记录）
  - 不计入 independent support
  - 不计入新增 strong 数量
  - 路由到 `independent_support_need` + `quote_ids_to_avoid_by_claim`
  - **不要**创建新的 unresolved question

`independent_support_need` 约束：
- 只针对 primary claim（importance="high"）
- 已有一条 verified strong/moderate support
- 仍有剩余 evidence budget
- 否则不为边缘 claim 反复搜索第二证据，避免浪费轮次

---

#### R1a: Method Quota 1→2

**文件**：`agent_system/environments/env_package/review/state.py`

Quote bank 构建（约 6614 行）：
- Per-source cap 中 method 从 1 提升到 2

**只改这一个点**，不改 source order、不改 snippet order、不改 prompt。跑 smoke test 观察 method evidence 的数量和质量变化。

---

#### R1b: Method Claim / Section Anchor 识别

**文件**：`agent_system/environments/env_package/review/state.py`

Method section anchor patterns（约 6189-6195 行）：
- 当前只匹配约 12 个特定 AI/ML 技术名（speculative decoding, routing, diffusion model 等）
- 增加通用 section-header 匹配：`Method`, `Approach`, `Architecture`, `Framework`, `Proposed Method`, `Our Method`
- **安全约束**：section heading 必须位于当前论文主体（不是引用其他工作的方法描述），且 quote 与 target claim 的 semantic alignment 足够高

Method claim 类型识别：
- 在 claim 初始化逻辑中确保 method/mechanism 类型的 claim 被正确标记 `claim_type="method"`
- 检查 `_build_review_task()` 或 claim extraction prompt 是否遗漏 method claim

---

#### R1c: Method Prompt 指导

**文件**：`agent_system/review_prompts.py`

Evidence Agent prompt（约 115-118 行）：
- 增加 method evidence 指导："When the paper describes a specific mechanism, architecture, or algorithmic step that directly supports a method-type claim, this evidence should cite the exact section/paragraph with a specific locator."
- 保持 strength 指导不变（method 默认 medium 合理）
- 增加："If the paper text contains a precise, verifiable description of how the method works (not just a name-drop), and the semantic alignment is high, `strength='strong'` is appropriate."
- 不删除 empirical 优先指导，但去掉"before generic method"的暗示

**评估标准**：如果 R1a + R1b + R1c 后 method evidence 的 semantic_alignment_score 能稳定达到 0.60+，则 promotion threshold 不需要调整。如果仍然大量低于 0.60，再考虑将 `METHOD_PROMOTION_STRONG_MIN_SCORE` 从 0.70 微调到 **0.65**（不是 0.62）。

---

#### R2: Recovery Target Hydration

**原则**：不改 validator；不允许 generic quote-bank evidence 做 claim downgrade；不默认重试 blocked patch。

**修正 R2 turn 条件矛盾**：

原方案中 `turn_id >= max_turns - 2` 与 `remaining_turns >= 3` 互相矛盾（`remaining_turns = max_turns - turn_id`，倒数两轮时 remaining <= 2）。修正为两个独立规则：

**规则 A — Pre-recovery negative preparation**：
```python
turn_id == max_turns - 3          # 倒数第 3 轮
and remaining_worker_turns >= 2
and grounded_negative_evidence_count == 0
and positive_support_inventory >= 2
and no_recent_analyze_flaws_action  # 避免重复
```
在 normal review 阶段主动路由到 `analyze_flaws`，做一次负面证据搜索。

**规则 B — Late one-shot precision retry**（仅限 negative evidence）：
```python
grounded_negative_count <= 1
and actionable_negative_count == 0
and remaining_turns >= 2
and positive_support_inventory 已满足
```
与常态 discovery（`== 0`）分开实现，是独立的 late retry 规则，不是修改同一个 override。

**Recovery intent 区分**：

不满足 claim downgrade 条件的证据不应用于 claim status change target。Target 带明确意图：
```python
{
    "target_claim_id": "...",
    "target_flaw_id": "...",
    "recovery_intent": "claim_status_change" | "flaw_downgrade" | "concern_refinement" | "limitation_routing",
}
```
不同 intent 使用不同 validator 路径：
- `claim_status_change`：要求 verified negative evidence 满足 downgrade 条件
- `flaw_downgrade`：允许 flaw 关联的 evidence（不要求 claim-level downgrade 条件）
- `concern_refinement`：允许 moderate negative evidence 细化 concern
- `limitation_routing`：允许 limitation 类 evidence 路由到 assessment_limitation

**Gate label `safe_blocked` 排序**：在 `_build_recovery_hydration_view()` 的 priority dict 中添加 `"safe_blocked": 4`。

---

#### R5: Negative Evidence Precision

**原则**：不追求数量，只追求 actionable precision。最后做，必须 budget-aware。

**文件**：`agent_system/environments/env_package/review/state.py`

`_classify_negative_evidence_type()`（约 6302 行）：
- 扩展为**组合型负向锚点** regex：`(lack|missing|insufficient|no|without|limited|lacking)` + `(evaluation|benchmark|experiment|ablation|baseline|comparison)`
- Regex 只生成 **candidate**，不直接判定 final type
- Final type 由 semantic verifier 确认（检查 quote 上下文是否确实描述了 evaluation 不足，而非"without requiring additional experiments"这类正向描述）

**文件**：`agent_system/review_manager_policy.py`

Negative evidence 触发拆分为两个独立规则：

**常态 discovery**（保持现有逻辑不变）：
```python
grounded_negative_evidence_count == 0
```

**Late one-shot precision retry**（新增独立函数，不修改现有 override）：
```python
grounded_negative_evidence_count <= 1
and actionable_negative_count == 0
and remaining_turns >= 2
and positive_support_inventory >= MIN_REQUIREMENTS
```
仅在 review 后期、正向支持已充足时触发一次。

---

### 安全边界总结

| 可以做 | 不要做 |
|---|---|
| T0 单独验证 truncation 行为 | truncation 和其他改动混在同一实验 |
| method quota 1→2 | method promotion threshold 大幅降低 |
| method section anchor 扩展 | method 提前到 results/table 之前 |
| method prompt 精确指导 | 删除 empirical 优先指导 |
| duplicate → superseded + audit trace | duplicate → 删除原始记录 |
| duplicate → independent_support_need | duplicate → 创建 unresolved question |
| question 创建端结构化（带 related_claim_ids） | bare string question |
| targetless question → internal_deferred | resolved_by_time_decay |
| gate label 新增 safe_blocked（priority=4） | safe_blocked 参与 reward/finalization 逻辑 |
| recovery intent 区分（claim/flaw/concern/limitation） | 不满足 downgrade 条件的证据做 claim downgrade |
| 组合型负向锚点 regex → candidate | regex 直接决定 final negative type |
| late one-shot precision retry（独立规则） | 修改常态 discovery 的 == 0 条件 |
| pre-recovery preparation（倒数第 3 轮，budget-aware） | 无条件重试 blocked recovery patch |
| targetless deferred rate 作为 WARN | 作为硬 FAIL 保护线 |
| method_support_ratio 作为观察指标 | 作为优化目标 |

### 验证命令

每步实施后运行：
```bash
# smoke test (8 papers, ~30 min)
conda run -n DrMAS-qwen35 env PYTHONPATH=/root/zssmas_mainline python3 scripts/run_review_infer.py \
  --model-path /reviewF/datasets/Qwen3___5-9B \
  --dataset-path ~/data/drmas_review --split test --limit 8 \
  --mode s4 --max-turns 7 --max-workers-per-turn 2 \
  --max-model-len 3072 --max-tokens 640 \
  --temperature 0.2 --top-p 0.95 --seed 20260604 --enforce-eager \
  --output-path outputs/results_exp/review_infer/p26_smoke_rN.jsonl \
  > logs/p26_smoke_rN.log 2>&1

# dashboard
conda run -n DrMAS-qwen35 env PYTHONPATH=/root/zssmas_mainline python3 scripts/dashboard_run_comparison_v1.py \
  --candidate outputs/results_exp/review_infer/p26_smoke_rN.jsonl \
  --label p26_rN --mode smoke
```
