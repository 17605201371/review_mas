# 真实负向证据定向发现计划书（2026-06-16）

## 0. 目标

本计划的目标不是增加“negative”计数，而是让系统稳定发现论文审稿中真正有价值的负向证据：

- missing_baseline
- missing_ablation
- insufficient_evaluation
- reproducibility_gap
- scope_overclaim
- result_claim_mismatch
- method_support_gap

核心原则：

> 负向问题从 claim 的证据义务中推导出来；负向证据必须回到论文原文 quote 验证；recovery 只围绕 verified negative flaw 发生。

这意味着 hard-negative diagnosis 不能替代 evidence formation。它只能生成“要查什么”的定向任务，不能直接产出 final flaw。

---

## 1. 当前结论

最新 hardneg20 A/B：

| 指标 | baseline qhyg | hardneg diagnosis | 结论 |
|---|---:|---:|---|
| overall protection | PASS | PASS | 保护线没破 |
| avg_reward | 0.4979 | 0.4540 | diagnosis 下降 |
| real_strong_support_total | 75 | 53 | support 被砍 |
| negative_evidence_candidate_count | 4 | 0 | 负向证据被压没 |
| verified_actionable_negative_flaw_count | 3 | 0 | actionable flaw 消失 |
| potential_concern_count | 3 | 0 | final concern 消失 |
| mark_contested_commit_count | 3 | 0 | contested 消失 |
| recovery_effective_repair | 3 | 0 | recovery 消失 |

判断：

1. `DRMAS_HARDNEG_DIAGNOSIS=1` 不能转正。
2. 失败原因不是模型不能判断，而是 routing 错了：它把 Critique 的模型判断放到了 Evidence quote 验证之前，导致没有可验证的 negative evidence。
3. 下一步应把 diagnosis 降级为 **target generator**，把 evidence formation 重新放回主路径。

---

## 2. 机制设计

### 2.1 从 claim 推导 evidence obligation

每个真实 claim 都需要先判定它“成立需要什么证据”。这是规则层 + 小范围模型判定共同完成的，不允许自由生成 generic concern。

| claim 信号 | required_evidence_type | 对应要查的负向问题 |
|---|---|---|
| outperform / better / SOTA / compare / benchmark | baseline_or_comparison | missing_baseline, result_claim_mismatch |
| result / accuracy / performance / evaluation | empirical_result | insufficient_evaluation, result_claim_mismatch |
| component / module / contribution / crucial / improves | ablation_or_component | missing_ablation |
| general / robust / across domains / broad claim | scope_coverage | scope_overclaim, insufficient_evaluation |
| training details / implementation / reproducible / data split | reproducibility_detail | reproducibility_gap |
| method / assumption / mechanism / objective | method_detail | method_support_gap |

输出不是 flaw，而是任务：

```json
{
  "task_id": "neg-search-claim-1-baseline",
  "claim_id": "claim-1",
  "negative_type": "missing_baseline",
  "required_evidence_type": "baseline_or_comparison",
  "search_question": "Does the paper compare this claimed improvement against appropriate baselines or prior methods?",
  "expected_quote_cues": ["baseline", "compare", "state-of-the-art", "prior method", "only compare", "no comparison"],
  "target_locator_hint": "Experiments / Results / Evaluation",
  "priority": 3,
  "source": "claim_evidence_obligation"
}
```

### 2.2 Evidence Agent 回到论文里找 quote

Evidence Agent 对每个 `targeted_negative_search_task` 只能输出两类结果：

1. 找到 paper quote：

```json
{
  "evidence_map": [
    {
      "evidence_id": "evidence-negative-claim-1-baseline-1",
      "claim_id": "claim-1",
      "stance": "weakens",
      "strength": "missing",
      "negative_evidence_type": "missing_baseline",
      "raw_quote": "The paper compares only against ...",
      "source_locator": "Section 4.2 / Table 2",
      "required_evidence_type": "baseline_or_comparison",
      "targeted_negative_search_task_id": "neg-search-claim-1-baseline",
      "binding_status": "bound_real_claim"
    }
  ]
}
```

2. 找不到 quote：

```json
{
  "unresolved_questions": [
    {
      "question": "No paper quote was found showing whether claim-1 has appropriate baseline comparison.",
      "target_type": "claim",
      "target_id": "claim-1",
      "targeted_negative_search_task_id": "neg-search-claim-1-baseline",
      "status": "not_assessable"
    }
  ]
}
```

严禁：

- 把 “not found” 直接算作 negative evidence。
- 把 abstract/general text 包装成 missing baseline。
- 把系统没看到、上下文不足、prompt 壳作为论文负向证据。
- 用 fallback/context claim 做 claim status patch。

### 2.3 Critique Agent 只绑定 verified negative evidence

Critique Agent 的任务从“自由诊断 flaw”改为：

- 读取 verified paper-negative evidence。
- 绑定到 flaw candidate。
- 标注 `grounding_status`。
- 不允许无 quote 直接升级为 verified flaw。

flaw 必须满足：

```text
claim_id
flaw_id
negative_evidence_ids
negative_quote
negative_type
locator
weakened_dimension
```

否则只能是 candidate / unresolved，不能进入 verified actionable negative flaw。

### 2.4 Recovery 围绕 verified flaw 执行

只有当 verified negative flaw 出现后，才触发 recovery：

| 状态 | recovery 操作 |
|---|---|
| claim 有 strong support，同时有 verified negative evidence | mark_contested |
| flaw 被过度升级，证据不足以 final weakness | downgrade_final_to_candidate |
| concern 是真实限制但不足以 claim downgrade | route_to_assessment_limitation |
| gap 已被后续 support 或 negative evidence 覆盖 | resolve_stale_gap |

优先恢复目标：

```text
mark_contested
resolve_stale_gap
downgrade_final_to_candidate
route_to_assessment_limitation
```

继续禁止：

```text
fallback/context claim status patch
synthetic claim downgrade
generic gap -> negative evidence
unsupported claim downgrade without verified negative evidence
```

---

## 3. 实施阶段

### P0：保留 diagnosis gate，新增 target-only 模式

新增开关：

```bash
DRMAS_TARGETED_NEGATIVE_SEARCH=1
```

语义：

- 不打开 `DRMAS_HARDNEG_DIAGNOSIS=1` 的 Critique 自由诊断路径。
- 只注入 `targeted_negative_search_tasks`。
- manager 路由到 Evidence Agent 的 `request_evidence_recheck`，不是 Critique Agent 的 `analyze_flaws`。

预期改动：

- `state.py`
  - 新增 `_targeted_negative_search_tasks(state, claims, max_items=4)`。
  - 基于 `_claim_required_evidence_types` 和 support profile 生成任务。
  - 在 evidence slice 中注入任务。
- `review_manager_policy.py`
  - hard-negative shortfall 时，如果开关开启，路由 Evidence Agent。
  - policy_source 可用 `targeted_negative_search_override`。
- `review_runner.py`
  - Evidence Agent observation 增加任务说明。
  - 强制 payload 只接受 quote-grounded negative evidence 或 not_assessable question。
- `review_prompts.py`
  - Evidence prompt 加入 target task contract。

验收：

```text
targeted_negative_search_task_count > 0
targeted_negative_search_not_assessable_count >= 0
negative_evidence_unlinked_to_flaw = 0
negative_evidence_overclaim = 0
protection PASS
```

### P1：Evidence Agent 负向任务 contract

Evidence Agent 对 `targeted_negative_search_tasks` 必须遵守：

```text
如果找到 quote：
  输出 negative evidence，必须带 raw_quote + locator + claim_id + negative_type + required_evidence_type。

如果找不到 quote：
  输出 unresolved/not_assessable，不算 negative evidence。
```

新增 validator / sanitizer：

- quote 缺失 → drop。
- locator generic → drop 或 unresolved。
- claim_id 非 real paper claim → drop。
- negative_type 与 task 不一致 → 降为 unresolved 或重新分类。
- raw_quote 只有章节标题/引用/future work → qhyg drop。

验收：

```text
targeted_negative_task_attempt_count >= 4 on smoke8
targeted_negative_quote_found_count >= 1 on smoke8
negative_evidence_candidate_count 不低于 baseline
verified_actionable_negative_flaw_count 不低于 baseline
```

### P2：Critique binding 与 final concern 打通

Critique 只处理已经过 verifier 的 negative evidence：

- `verified_negative_evidence_ids`
- `targeted_negative_search_task_id`
- `claim_id`
- `negative_type`
- `locator`

目标：

```text
verified negative evidence -> verified potential concern -> final potential concern
```

重点防止之前的问题：

```text
verified_potential_concern_count > 0
但 potential_concern_count = 0
```

验收：

```text
verified_actionable_negative_flaw_count >= baseline
verified_potential_concern_count >= baseline
potential_concern_count >= baseline
grounded_weakness_count 不强推
negative_evidence_unlinked_to_flaw = 0
```

### P3：Recovery lifecycle 恢复

当 P2 有 verified negative flaw 后，恢复 recovery 操作：

- `mark_contested`
- `resolve_stale_gap`
- `downgrade_final_to_candidate`
- `route_to_assessment_limitation`

验收：

```text
mark_contested_commit_count > 0
recovery_effective_repair >= baseline - 1
recovery_no_effect_commit = 0
recovery_harmful_commit_risk = 0
target_gate_negative_verified_target_turns > 0
```

### P4：hardneg20 A/B

先 smoke8，再 hardneg20：

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 DRMAS_TARGETED_NEGATIVE_SEARCH=1 ...
```

对比 baseline qhyg：

```text
support 不显著退化
negative evidence 不下降
verified actionable flaw 上升或持平
potential concern 上升或持平
recovery 不下降
protection PASS
```

不达标就不进入 full39。

### P5：清理已证实无效的 hard-negative diagnosis 代码

前置条件：

- `DRMAS_TARGETED_NEGATIVE_SEARCH=1` 在 smoke8 / hard_negative_20 上证明不压低 support、negative evidence、recovery。
- 指标至少不低于 qhyg baseline：`negative_evidence_candidate_count`、`verified_actionable_negative_flaw_count`、`potential_concern_count`、`mark_contested_commit_count`、`recovery_effective_repair` 不退化。
- protection 仍为 PASS，且 `negative_evidence_unlinked_to_flaw = 0`、`negative_evidence_overclaim = 0`。

清理范围：

- 移除或归档 `DRMAS_HARDNEG_DIAGNOSIS` 的 Critique 自由诊断路径。
- 删除 `hard_negative_diagnosis_targets` / `hard_negative_diagnosis_rule` 的 live slice 注入。
- 删除 Critique prompt 中直接诊断 flaw 的 hard-negative 增强文本。
- 删除只服务旧 diagnosis 路径的 tests，保留 claim-target gate 中对 context/fallback/leakage 的安全测试。
- 保留可复用的 claim evidence obligation / target eligibility helper，迁移到 targeted search 命名，避免历史失败路径继续影响论文叙事。

不清理：

- qhyg quote hygiene。
- fallback/context claim patch guard。
- negative evidence verifier / binding guard。
- recovery validator。

判断：

> 旧 diagnosis 失败点在于把模型判断放到 paper quote 验证之前；新路径稳定后，应把旧路径清掉，避免后续实验误开 `DRMAS_HARDNEG_DIAGNOSIS=1` 再次压没负向证据和 recovery。

---

## 4. 指标目标

### smoke8 最小验收

```text
overall protection = PASS
negative_evidence_candidate_count >= baseline
verified_actionable_negative_flaw_count >= baseline
potential_concern_count >= baseline
mark_contested_commit_count >= baseline 或 >0
recovery_effective_repair >= baseline - 1
negative_evidence_unlinked_to_flaw = 0
recovery_harmful_commit_risk = 0
```

### hardneg20 最小验收

```text
overall protection = PASS
real_strong_support_total >= baseline - 10%
negative_evidence_candidate_count >= baseline
verified_actionable_negative_flaw_count >= baseline
potential_concern_count >= baseline
contested_relation_effective_count >= baseline
recovery_effective_repair >= baseline - 1
targetless_unresolved_deferred_count = 0
negative_evidence_unlinked_to_flaw = 0
state_contamination_count = 0
recovery_no_effect_commit = 0
recovery_harmful_commit_risk = 0
```

### 理想目标

```text
negative_evidence_candidate_count >= 8 on hardneg20
verified_actionable_negative_flaw_count >= 5 on hardneg20
potential_concern_count >= 5 on hardneg20
mark_contested_commit_count >= 3
recovery_effective_repair >= 3
至少出现 2 类真实负向类型：
  missing_baseline / missing_ablation / insufficient_evaluation /
  reproducibility_gap / scope_overclaim / result_claim_mismatch
```

---

## 5. 风险与护栏

### 风险 1：任务生成过多，挤压 support

护栏：

```text
每篇最多 4 个 targeted_negative_search_tasks
每个 claim 最多 2 个 negative tasks
已有 strong support 不代表跳过负向任务，但降低优先级
max-turns=7 下最多触发 1 次 targeted negative Evidence pass
```

### 风险 2：模型把没找到证据说成缺失证据

护栏：

```text
not_found -> unresolved/not_assessable
只有 raw_quote + locator 才能入 negative evidence
```

### 风险 3：generic gap 冒充 negative evidence

护栏：

```text
negative_type=generic_gap 不计 actionable
generic locator 不计 verified
system/context wording 直接 drop
```

### 风险 4：fallback/context claim 污染 recovery

护栏：

```text
targeted task 只能绑定 real paper claim
fallback/context claim 可以作为 salvage content，但不能 status patch
recovery_validator 继续拦 fallback/context claim downgrade
```

---

## 6. 开发顺序

1. 新增 `DRMAS_TARGETED_NEGATIVE_SEARCH` 开关，默认关闭。
2. 实现 `_targeted_negative_search_tasks`，只生成任务，不改 state。
3. Evidence slice 注入任务。
4. Evidence prompt 增加 contract。
5. sanitizer/validator 强制 quote-grounded negative evidence。
6. Critique binding 只消费 verified negative evidence。
7. Recovery 重新接入 verified negative flaw。
8. smoke8 验证。
9. hardneg20 A/B。
10. dashboard + case audit。

---

## 7. 不做的事

当前阶段不做：

- 不转正 `DRMAS_HARDNEG_DIAGNOSIS=1`。
- 不让 Critique 自由生成 verified flaw。
- 不强推 grounded weakness。
- 不放开 claim downgrade。
- 不把 not_found 算 negative evidence。
- 不继续堆 support 来掩盖负向问题。

---

## 8. 一句话执行策略

把“负向诊断”从 Critique 的自由判断，改造成 Evidence Agent 的定向查证任务：

```text
claim obligation -> targeted negative search task -> paper quote -> verified negative flaw -> contested/recovery
```

这才符合论文主线：结构化 ReviewState、真实 paper-grounded negative evidence、可审计 recovery lifecycle。
