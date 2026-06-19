# P26 Negative Discovery 压制点代码定位（交付书第 7 节落地清单）

针对交付书第 7 节"代码层面疑似压制原因"，逐条给出**确切文件 / 行号 / 当前实现 / 改法**。
全程不碰 claim downgrade。每条都标注了与交付书的对应关系和一个重要修正：**部分压制点在 guard3 commit `3342192` 中已经被改过**，下面据实更正。

> 说明：本清单只做定位与改法建议，未改任何代码。实施前请先跑 P0（hardneg20 guard3），用真实数据确认瓶颈到底在哪一层。

---

## 7.1 Target cap —— **大部分已修复，无需再动**

交付书担心 `target_flaw/claim/evidence` cap 仍为 2。实测 guard3 已经把它们提到 4：

`agent_system/review_manager_policy.py:57-59`
```python
_NEGATIVE_TARGET_FLAW_LIMIT = 4       # 已是 4（交付书建议 hardneg=4 ✓）
_NEGATIVE_TARGET_EVIDENCE_LIMIT = 4   # 已是 4 ✓
_NEGATIVE_TARGET_CLAIM_LIMIT = 2      # 保持 2（交付书要求不放宽 claim downgrade ✓）
```

**结论**：flaw/evidence target cap 已满足交付书要求；claim cap 故意保留 2，正确。

**唯一可选改动**：当前是全局常量，不区分 smoke8/hardneg20/full39。若要做交付书建议的 mode-aware（smoke=2 / hardneg=4 / full39=3），需把这三个常量改成按 dataset/mode 解析的函数，并在 `_verified_negative_flaw_review_targets()`（同文件 259-319 行）传入。**但 flat=4 已经覆盖 hardneg 需求，优先级低，先不动。**

其余 `[:2]` 散落点（如 `review_runner.py` 的 `supporting_evidence_ids[:2]`）是单条 flaw 的证据展示截断，不是发现上限，**不要动**。

---

## 7.3 Hard-negative discovery "达标即停" —— **核心瓶颈，这里才是数量上不去的主因**

`agent_system/review_manager_policy.py:60-63`
```python
_HARD_NEGATIVE_DISCOVERY_GROUNDED_TARGET = 3     # 攒满 3 条 grounded negative 就不再补充发现
_HARD_NEGATIVE_DISCOVERY_ACTIONABLE_TARGET = 2   # 攒满 2 条 actionable 就停
_HARD_NEGATIVE_DISCOVERY_VERIFIED_FLAW_TARGET = 2
_HARD_NEGATIVE_DISCOVERY_MAX_ATTEMPTS = 3        # 最多 3 次补充 pass
```

停止判据在 `_hard_negative_discovery_shortfall_reasons()`（440-451 行）：三项都达标 → 返回空 → 不再触发发现。
补充发现的门控在 `_allow_supplemental_hard_negative_discovery()`（382-395 行）：
```python
if remaining_after_current is None or remaining_after_current < 2:   # 剩余轮数 < 2 直接放弃
    return False
if attempt_count <= 0 or attempt_count >= _HARD_NEGATIVE_DISCOVERY_MAX_ATTEMPTS:  # 超过 3 次放弃
    return False
if not _hard_negative_discovery_shortfall_reasons(state):           # 达标就放弃
    return False
```
实际触发在 `apply_manager_policy_fallback()` 的 `hard_negative_discovery_override`（约 2306-2345 行），还叠加了 `budget_aware_skip`（2298-2304 行：`remaining_after_current < 1` 或 `< 2 且 positive 未就绪` 就跳过）。

**为什么数量低**：三重夹击——(a) 目标只要求每篇 3 grounded / 2 actionable；(b) 最多 3 次 pass；(c) mt7 下轮数预算紧张，常常 `remaining_after_current < 2` 直接被 `budget_aware_skip` 砍掉，late discovery 跑不起来。

**改法（按交付书 7.3 "negative_evidence_enrichment_pass，只追加 evidence 不改 claim status"）**：
1. 提高停止目标（最直接）：`GROUNDED_TARGET 3→5`、`ACTIONABLE_TARGET 2→3`，让 shortfall 在 hardneg 场景持续为真。建议做成 mode-aware（仅 hardneg/full39 提高，smoke8 保持）。
2. 放宽 `MAX_ATTEMPTS 3→4或5`，并把 `_allow_supplemental_*` 的 `remaining_after_current < 2` 改为 `< 1`（只要还有 1 轮就允许补一次纯 enrichment）。
3. 新增独立的 `negative_evidence_enrichment_override`（不复用现有 discovery override），触发条件 = shortfall 仍在 + 还有 ≥1 轮 + 本轮不是 recovery phase；它只路由到 `request_evidence_recheck` 追加 negative evidence，**不设置任何 claim/flaw status patch 字段**。
4. **安全约束**：enrichment pass 产出的 evidence 必须照常过 `_is_grounded_paper_negative_evidence_record`（要求 raw_quote+locator+real-claim binding），不会破坏 hygiene。

---

## 7.2 Negative quote bank 容量 —— **已不算"太少"，瓶颈在召回/绑定不在容量**

`agent_system/environments/env_package/review/state.py`
- `_build_critique_negative_quote_bank(body, max_quotes=6)`（7469 行，调用处 7691/8461）：bank 容量已是 **6**，高于交付书建议的 3。
- `_prompt_negative_quote_bank_entries(quote_bank, max_items=5)`（8222 行，调用处 8469）：prompt 里最多展示 **5** 条负向 quote。

**结论**：容量不是瓶颈。真正限制是"bank 里的 6 条有多少能通过 semantic verifier 变成 grounded actionable negative"。所以 7.2 的实际功夫应落在：
- 7.5 的类型分类（让更多 quote 落到 actionable 类型而非 scope_limitation/generic_gap）；
- 7.3 的持续发现（让模型真去用这些 quote 形成 flaw）。
**不建议**盲目把 max_quotes 再调大——会增加噪声，挤占 prompt。

---

## 7.4 Terminal concern 阻断后续 enrichment —— **确认是 bug 式压制，可安全修**

`agent_system/review_manager_policy.py:281`（在 `_verified_negative_flaw_review_targets` 内）
```python
if not flaw_id or flaw_id in terminal_flaw_ids:
    continue          # ← terminal flaw 被整体跳过，无法再追加任何 negative evidence
```
`terminal_flaw_ids` 来自 `_recent_terminal_recovery_flaw_ids()`（230-256 行），标记依据 `recovery_terminal` / `PROTECTED_POTENTIAL_CONCERN_TERMINAL_REASON` / `ACTIONABLE_CONCERN_PRESERVED`。
state 侧的 terminal 落定在 `state.py:5933-5938, 5973-6008, 6183-6184`。

**改法（按交付书 7.4：terminal flaw 不允许 status patch / claim downgrade，但允许 evidence enrichment + contested_relation evidence list 扩展）**：
- 把 281 行的"整体跳过"拆成两类目标：当目标用途是 **status patch / claim downgrade** 时跳过 terminal flaw（保持现状）；当用途是 **evidence enrichment / contested evidence 扩展** 时**不跳过**，允许继续给它绑新 negative evidence。
- 具体做法：给 `_verified_negative_flaw_review_targets` 增加参数 `purpose: Literal["status_patch","enrichment"]`，enrichment 模式下不读 `terminal_flaw_ids`；并在 recovery_validator 侧确保 terminal flaw 收到 enrichment patch 时只允许 `evidence_ids` 增补、拒绝 status 变更。
- **安全约束**：terminal 的 status / claim 仍冻结，只放开"加证据"，不会引入 harmful recovery。

---

## 7.5 负向类型分类过度归入 scope_limitation —— **分类器是 quote-only，缺 claim 上下文**

`agent_system/environments/env_package/review/state.py:7067` `_classify_negative_evidence_type(quote: str)`
- 纯 regex、**只吃 quote 文本**，无 claim 上下文。顺序匹配后 fall-through 到 `scope_limitation`（7103）或 `generic_gap`（7106）。
- 类型集合（7116-7127）：
  - ACTIONABLE = {direct_contradiction, negative_result, missing_ablation, missing_baseline, insufficient_evaluation, scope_overclaim, result_claim_mismatch}
  - LIMITATION（非 actionable）= {scope_limitation, reproducibility_gap, generic_gap}
- 记录级入口 `_negative_evidence_type_for_record(record)`（7130）：也只读 record 自身的 quote/stance，不看关联 claim。

**改法（按交付书 7.5 二次分类，需要 claim 上下文）**：
- 新增 `_reclassify_negative_with_claim_context(quote, claim_item, base_type)`，在 `_negative_evidence_type_for_record` 之后调用（或在 merge 时对每条 negative evidence 跑一遍），规则：
  - broad/绝对化 claim（"always/all/state-of-the-art/general"）+ 具体 limitation quote → `scope_overclaim`
  - broad performance claim + mixed/下降结果 quote → `result_claim_mismatch`
  - method/实现依赖 claim + 缺实现/超参/代码 quote → `reproducibility_gap`（注意：reproducibility_gap 当前在 LIMITATION 集合，若要让它算 actionable 需同时调整集合归属——这一步要谨慎，先观察）
  - broad evaluation claim + 单数据集/单任务 quote → `insufficient_evaluation`
  - component/contribution claim + 无 ablation → `missing_ablation`
- **安全约束**：reclassify 只能把 scope_limitation/generic_gap **升级**到 actionable，且必须同时满足 quote 有 locator + 绑定 real claim；不能把 neutral_control_context / noise 升级。最终类型仍由 semantic verifier 把关。

---

## 7.6 Final-view 强度层级缺 actionable_major_concern + resolve_stale_gap 未触发

### (a) 缺 actionable_major_concern 层
`agent_system/environments/env_package/review/state.py` `_classify_flaw_final_view_layer(flaw, state)`（约 4640-4675）：
```python
actionable_ids = _verified_actionable_negative_evidence_ids_for_flaw(flaw, state)
if actionable_ids:
    if status == "confirmed":
        return "grounded_weakness"
    # 注释明确说：故意不设"中间专属层"，让它回落到 potential_concern
    return "potential_concern"
```
对应统计在 `build_decision_hygiene_view`（4517 起），分层 4730-4743：actionable 但未 confirmed → 记 `verified_potential_concern`，并写 `negative_flaw_not_upgraded_reason`。

**改法（按交付书 7.6：新增 actionable_major_concern，不改 claim status）**：
- **关键**：交付书要 additive，不能像历史那样用"专属互斥层"导致它不进 potential_concern_count（4660 行注释正是为此回滚过）。所以**不要**改 `_classify_flaw_final_view_layer` 的返回值，而是**新增一个并行 flag**：当 `actionable_ids and status != "confirmed"` 时给 flaw 打 `flaw["actionable_major_concern"] = True`，并在 hygiene view 里加一个 `actionable_major_concern_count`（与 potential_concern_count 共存、不互斥）。
- final report 渲染时把带该 flag 的条目用更强措辞表达拒稿理由（仍不改 claim status / decision）。

### (b) resolve_stale_gap 已存在但触发 0 次
- operation 已实现：dashboard 有 `recovery_patch_operation_resolve_stale_gap_turns`（guard3 = 0）；state 侧有 `can_resolve_assessment_limitation`（state.py:320-325）和 stale gap → assessment_limitation 的处理（3488）。
- 说明机制在，但**触发条件没满足**。交付书 P1 的触发条件：gap is open，且同 claim 后续已有 verified strong support，或 gap 已被 verified evidence superseded。

**改法**：在 recovery 路由里新增 `resolve_stale_gap` 的主动触发——扫描 open/stale gap，若其 related claim 现在已有 verified strong support，则路由一个 resolve_stale_gap patch。挂载点同 7.3 的 override 区（review_manager_policy.py ~2200-2345），作为 recovery operation diversity 的第一个安全增量。**先不要**碰 downgrade_final_to_candidate / downgrade_claim_to_unsupported。

---

## 实施优先级（与交付书一致）

1. **先跑 P0 hardneg20 guard3**，用真实数据确认瓶颈层（很可能落在 7.3 + 7.5）。
2. 若 hardneg20 负向数量仍低，按此顺序改、每次只改一点再跑 smoke 验证：
   **7.3 提高 discovery 停止目标 + enrichment pass** → **7.5 claim-aware 二次分类** → **7.4 terminal 放开 enrichment** → **7.6(a) actionable_major_concern flag**。
3. P1：打通 **7.6(b) resolve_stale_gap**。
4. 始终守住：state_contamination=0、recovery_harmful_commit_risk=0、recovery_no_effect_commit=0、不碰 claim downgrade。
