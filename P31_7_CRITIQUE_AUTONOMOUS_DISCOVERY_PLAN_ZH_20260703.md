# P31.7 Critique 自主候选发现修复计划

日期：2026-07-03

正确工作目录：

```text
/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524
```

不要在废弃目录 `/Users/zss/Downloads/DrMAS-master` 上继续推进。

## 1. 当前判断

需要修改 Critique 作为自主候选生成器的链路。

当前 P31.6 fresh full20 结果说明，系统已经能产出数量足够的 verified review issues，但这些 issue 主要来自 deterministic seeds，而不是 Critique payload：

```text
verified_review_issue_count = 29
quote_duplicate_merged_verified_review_issue_cluster_count = 20
reviewer_candidate_review_issue_critique_payload_count = 1
reviewer_candidate_review_issue_deterministic_seed_count = 25
critique_payload_verified_cluster_count = 1
candidate_menu_item_used_count = 4
candidate_menu_item_verified_count = 0
mark_contested_commit_count = 8
protection_passed = True
```

结论：

- 如果目标只是让系统产出 verified issue，当前 deterministic seed + strict verifier 已经能做到。
- 如果论文要声称 Critique 可以自主发现审稿缺陷，当前还不能成立。
- P32 仍然阻塞，不能把当前结果写成 autonomous Critique discovery solved。

## 2. 根因判断

### 2.1 Critique 被改成了复杂菜单填写器

当前 Critique discovery turn 同时要求：

- 查看 selector menu；
- 选择或拒绝 menu item；
- 复制 `candidate_menu_id`；
- 填 `claim_id` / `issue_type` / `required_evidence_type` / `expected_entity` / `obligation_id`；
- 附带 `observed_inventory`；
- mirror 到 `review_issue_candidates`；
- 保持固定 slot schema。

这对 MiMo 这类小模型过重。它名义上在“自主发现”，实际更像在填一张复杂表单。

### 2.2 deterministic seed 掩盖了 Critique 失败

runner 会在 Critique 输出不足时自动 top-up 到 12 个 deterministic candidates。最终 dashboard 数量很好看，但来源被 seed 主导：

```text
reviewer_candidate_review_issue_deterministic_seed_count = 25
critique_payload_verified_cluster_count = 1
```

这会让系统看起来进步明显，但不能支撑“Critique 自主发现”叙事。

### 2.3 selector menu 太小且反馈不足

P31.6 里 `candidate_menu_item_used_count=4`，但 `candidate_menu_item_verified_count=0`。说明 Critique 确实尝试用菜单，但选中的项没有过 verifier。失败原因没有回流给下一轮 Critique，因此没有形成学习式闭环。

### 2.4 不应通过放宽 verifier 解决

当前 protection 线全 PASS，是系统最重要的安全基础。下一步不应放松 verifier，不应把 generic gap、retrieval/context gap、author limitation 或 Critique 纯判断直接算 verified issue。

## 3. P31.7 目标

P31.7 的目标不是继续提高总 issue 数量，而是让 Critique-origin issue 真正成立。

GPT 建议中“不要继续把 29/19 做高，而是围绕 P31.6 暴露问题做质量闭环”的方向应采纳。因此 P31.7 拆成两个连续子阶段：

```text
P31.7A Audit-Fix：先把 P31.6 结果审计、口径和 regression guard 固化。
P31.7B Critique Autonomy：再修改 Critique discovery interface 和 fresh rerun。
```

如果 P31.7A 发现 P31.6 的 19 个 system clusters 中 D 类过多、cluster count 口径不一致、或关键 protection/recovery 口径有误，则不要先改 prompt，也不要进入 P31.7B。

验收目标：

```text
critique_payload_verified_cluster_count >= 3
candidate_menu_item_verified_count >= 2
manual A/B Critique-origin clusters >= 3
manual_D_clusters = 0
unfilled_manual_audit_clusters = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
protection_passed = True
```

仍然不进入 P32，除非同时满足机器 gate 和人工 A/B 审计。

## 4. P31.7A：审计闭环前置项

### 4.1 生成正式 manual cluster audit artifact

P31.6 当前只能算 pipeline checkpoint，不能直接作为论文主结果。需要先生成 cluster-level 人工审计文件：

```text
P31_6_FRESH_20260703_212637_MANUAL_CLUSTER_AUDIT.md
P31_6_FRESH_20260703_212637_MANUAL_CLUSTER_AUDIT.json
```

审计对象是 system clusters，不是 29 rows。每个 cluster 至少包含：

```text
paper_id
cluster_id
issue_type
target_entity
origin: critique_payload / deterministic_seed / claim_obligation / quote_grounded
manual_label: A/B/C/D
manual_merge_target
raw_paper_evidence_checked
counterevidence_checked
downgrade_reason
paper_facing_usable: yes/no
```

dashboard 需要报告：

```text
system_rows
system_clusters
manual_A_clusters
manual_A_B_clusters
manual_C_clusters
manual_D_clusters
critique_origin_A_B_clusters
deterministic_seed_A_B_clusters
```

### 4.2 统一 cluster count 口径

P31.6 dashboard / case table 之间存在 cluster count 口径风险：

```text
verified_review_issue_cluster_count = 19
verified_review_issue_cluster_recomputed_count = 20
quote_duplicate_merged_verified_review_issue_cluster_count = 20
case table displayed clusters = 19
```

P31.7A 必须先统一：

```text
row_count - duplicate_row_count = displayed_cluster_count
case_table_cluster_count == dashboard_cluster_count
origin_cluster_counts sum == displayed_cluster_count
quote_duplicate_merged_cluster_count <= system_cluster_count
```

若 direct quote lane 需要单独合并，应显式命名，不得和 obligation-grounded system cluster count 混用。

### 4.3 高风险 cluster regression guards

为 P31.6 审计中暴露的 C/D 风险建立 reject/downgrade regression tests。重点样例：

```text
7Dub7UXTXN / efficiency_resource_measurement
7Dub7UXTXN / robustness_learning_rate
cklg91aPGk / held-out coverage for GCL
fGXyvmWpw6 / data_with_the_latest_network
xUe1YqEgd6 / transformer-based_network
ye3NrNrYOY / domain_causal_representation
ye3NrNrYOY / aspects_the_causal_mechanism
HPuLU6q7xq / LoRA module
```

需要新增或确认的规则：

- 理论学习动态、loss landscape、证明型 claim 不自动要求 runtime/memory/FLOP/hardware。
- 理论 claim 不自动产生 learning-rate / width / dataset variation robustness 义务，除非论文明确 claim robustness/generalization。
- 如果全文已有 heterophily、large-scale、多 benchmark、node-classification coverage，不应继续判 generic held-out coverage gap。
- malformed target 降级：`data_with_the_latest_network`、`aspects_the_causal_mechanism`、`transformer-based_network`、`ranch_encoder` 等不能直接 verified，除非能归一化到 paper-named contribution entity。
- 普通 transformer/network/module 不自动成为 missing-ablation target，除非它是论文命名贡献或核心机制，且没有已有 ablation 覆盖。
- causal mechanism / representation 这类抽象概念必须绑定到可实验隔离的具体 mechanism，否则降为 potential concern。
- 标准工具或通用适配模块如 LoRA 不能自动成为 contribution-bound missing ablation，除非论文把它作为主要创新。

### 4.4 Positive controls

以下 cluster 可作为 guard 不应误杀的正例，但只能按 cluster 计数，不能按 row 膨胀：

```text
WpXq5n8yLb / recurrent_draft_model
NnExMNiTHw / acceptance_prediction_head
mHv6wcBb0z / generalized_noise_regularization
XH3OiIhtvf / secure aggregator result-claim mismatch
a6SntIisgg / local/global/fusion mechanism, if raw paper confirms it is a contribution
```

### 4.5 Clean provenance 前置要求

P31.6 fresh run 仍不能作为最终 paper-facing clean result。P31.7B fresh rerun 之前需要保证：

```text
code_dirty = clean
code_commit = fixed current commit
manual audit artifact present
dashboard/case cluster count consistent
protection PASS
recovery_harmful_commit_committed = 0
```

P31.7 的成功标准不看总 rows 增长，而看：

```text
manual_A_B_clusters >= 8
manual_D_clusters <= 3
critique_origin_manual_A_B_clusters >= 3
critique_origin_D_clusters = 0 或 <= 1, 但任何 D 都必须解释并不能进 paper-facing 主表
```

## 5. P31.7B：Critique 变成轻量 selector/reasoner

### 5.1 扩大并重排 selector menu

将 Critique-visible selector menu 从“小 top-K”改成 slot-balanced menu：

```text
总菜单项：10-12
每个 issue type 至少尝试覆盖：
- missing_baseline
- missing_ablation
- scope_or_robustness
- protocol_or_reproducibility
- efficiency_cost
- result_claim_mismatch
每个 claim 最多 2 个 item
每个 issue type 最多 3 个 item
```

菜单 item 必须仍然来自 verifier-ready substrate：

```json
{
  "candidate_menu_id": "...",
  "claim_id": "...",
  "issue_type": "...",
  "expected_entity": "...",
  "obligation_id": "...",
  "inventory_anchor": {
    "quote": "...",
    "locator": "...",
    "inventory_type": "..."
  },
  "why_review_worthy": "...",
  "known_rejection_risks": ["already_observed", "generic_target", "weak_inventory"]
}
```

菜单仍然只是候选提示，不是 evidence。

### 5.2 简化 Critique 输出契约

Critique discovery turn 只要求输出：

```json
{
  "selected_menu_items": [
    {
      "candidate_menu_id": "rim-c...",
      "decision": "selected|reject",
      "rationale": "...",
      "confidence": 0.0
    }
  ],
  "freeform_review_issue_candidates": [
    {
      "claim_id": "...",
      "issue_type": "...",
      "missing_or_weak_items": ["..."],
      "observed_inventory": [{"quote": "...", "locator": "..."}],
      "rationale": "..."
    }
  ]
}
```

Critique 不再需要同时 mirror 成完整 `review_issue_candidates`。runner 负责把 selected menu item 展开成 verifier-ready candidate。

### 5.3 selected-menu 展开由 runner/state 统一完成

runner 对 `selected_menu_items` 做确定性展开：

- 只接受当前 state 中存在的 `candidate_menu_id`；
- 复制 menu item 的 claim/obligation/entity/inventory anchor；
- 标记 `discovery_origin=critique_payload_menu_selected`；
- 进入原有 strict bundle verifier；
- 如果 menu item 已经过期或被 guard 过滤，记录失败原因，不 reinterpret 成 free-form issue。

### 5.4 free-form candidate 降权但保留

允许 Critique 提出 free-form candidate，但必须满足：

```text
concrete missing/mismatch entity
AND real claim_id
AND copied observed inventory anchor
AND not retrieval/context gap
```

free-form candidate 若不能绑定 menu/obligation，只能进入 diagnosis_pending，不计 verified issue。

### 5.5 Critique payload 结构要求

下一轮不是让 Critique “多提问题”，而是让它输出更可验证的结构。推荐最小字段：

```text
claim_anchor
target_entity
issue_type
expected_evidence
observed_inventory
possible_counterevidence_aliases
why_existing_inventory_does_not_cover
```

这些字段仍然是候选信息，不是 verified evidence。最终是否计入 verified issue 仍由 strict bundle verifier 决定。

## 6. 评估隔离：新增 Critique-only discovery mode

为了判断 Critique 是否真的进步，需要加一个评估开关：

```bash
DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL=1
```

该模式下：

- 禁用 deterministic seed top-up，或将 top-up 延迟到 Critique 失败后的单独阶段；
- dashboard 单独报告 Critique-only 指标；
- 不把 seed 结果混入 Critique-origin 成功率。

建议新增指标：

```text
critique_only_candidate_count
critique_only_selected_menu_count
critique_only_verified_count
critique_only_verified_cluster_count
critique_only_rejected_by_reason
seed_topup_after_critique_failure_count
```

常规 full20 仍可保留 seed top-up 用于系统性能；但论文中 Critique 自主发现能力必须看 Critique-only 或 origin-separated 指标。

## 7. 失败反馈闭环

将上一轮 selector/menu failure summary 暴露给下一轮 Critique：

```json
{
  "recent_menu_failure_summary": [
    {
      "candidate_menu_id": "...",
      "expected_entity": "...",
      "failure_reason": "missing_entity_already_observed_in_inventory",
      "lesson": "Do not select an absence issue when the inventory already covers the target."
    }
  ]
}
```

只暴露短摘要，不暴露 full logs，避免 prompt 膨胀。

## 8. Recovery 红线

P31.6 的 recovery 方向正确：保持 non-destructive `mark_contested`，不要让 claim downgrade 或 unsupported status patch 重新进入主线。

下一轮必须继续报告并守住：

```text
recovery_harmful_commit_committed = 0
downgrade_claim_to_unsupported_turns = 0
verified_issue_repair 单独计数
effective_repair_without_verified_issue 单独计数
```

论文口径只能写：

```text
8 non-destructive mark_contested commits, including 6 tied to verified review issue evidence
```

不能写成：

```text
8 verified issue repairs
```

## 9. 不做的事

本阶段明确不做：

- 不放宽 quote-grounded negative verifier；
- 不把 Critique/model judgment 直接算 verified issue；
- 不把 generic “more evaluation / stronger baseline / ablation evidence” 算 verified issue；
- 不把 author limitation、future work、retrieval/context/truncated-material gap 算 verified issue；
- 不为了达到数量目标提高 deterministic seed 数量；
- 不进入 P32，直到 Critique-origin 机器 gate 和人工 A/B gate 都通过。

## 10. 实现重点

主要改动位置：

```text
agent_system/environments/env_package/review/state.py
agent_system/inference/review_runner.py
agent_system/review_prompts.py
scripts/p31_6_entry_gate_audit.py
scripts/p31_6_status_report.py
tests/
```

具体任务：

1. 生成 P31.6 manual cluster audit artifact。
2. 统一 dashboard / case table cluster count 口径。
3. 为高风险 C/D clusters 添加 regression tests。
4. 输出 cluster-level origin + manual label 指标。
5. 扩展 `_review_issue_candidate_selector_menu`，支持 slot-balanced 10-12 item menu。
6. 简化 `render_critique_observation` 中 review issue discovery contract，让 `selected_menu_items` 成为主输出。
7. 修改 `_maybe_recover_selected_review_issue_menu_items`，让 selected-menu 展开成为唯一主路径，不要求 Critique mirror 完整 candidate。
8. 增加 `DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL`，隔离 Critique-only 结果与 seed top-up 结果。
9. 增加 selector failure summary 到 Critique state slice。
10. dashboard / case table / entry gate 增加 Critique-only、selected-menu verified、manual audit 指标。
11. 更新测试，确保 verifier 仍然严格。

## 11. 测试计划

### Unit tests

- selected menu item 可以展开成 verifier-ready candidate。
- stale / hallucinated `candidate_menu_id` 被拒绝。
- selected menu item 过期后不会被 reinterpret 成 free-form candidate。
- Critique-only eval 下 deterministic seed 不混入 Critique-origin 指标。
- generic target、retrieval/context gap、author limitation 仍被拒绝。
- selected-menu verified issue 仍必须满足 claim anchor + inventory anchor + concrete missing item + no counterevidence。

### Offline checks

用最新 `P31_6_FRESH_20260703_212637` raw 做 current-code recompute：

```text
目标不是改变旧 raw 的 Critique 输出，而是确认：
- 新指标能正确分离 Critique-only / seed-topup；
- 旧 selected_menu failures 被正确归因；
- protection 不回退。
```

### Fresh full20

用 MiMo full20 跑新版本：

```text
API_MAX_WORKERS=4
MAX_TURNS=7
MAX_TOKENS=1536
API_MAX_RETRIES=8
API_TIMEOUT=600
```

验收：

```text
critique_payload_verified_cluster_count >= 3
candidate_menu_item_verified_count >= 2
manual A/B Critique-origin clusters >= 3
manual_D_clusters = 0
protection_passed = True
```

## 12. 论文叙事口径

如果 P31.7 达标，论文可写：

> Critique does not directly verify flaws. It selects or proposes verifier-ready review issue candidates over claim-obligation and paper-inventory contrasts. The state verifier then admits only candidates with locatable claim anchors, inventory anchors, concrete missing/mismatch targets, and no full-text counterevidence.

如果 P31.7 不达标，论文应写：

> The current system can verify high-quality review issue bundles, but autonomous Critique discovery remains an open bottleneck; deterministic entity/inventory seeds are necessary to reach stable coverage.

该失败本身也可作为论文讨论，不应通过放宽 verifier 掩盖。

## 13. 本轮执行结果 2026-07-03

P31.7A 已落地：

```text
manual audit = cluster-level template/validation
dashboard/case cluster count = current-code recompute, consistent
seed-carried menu ids = no longer counted as Critique-selected menu success
high-risk false-positive guards = retained / extended
protection lines = PASS
```

P31.7B 第一版已落地但未达 gate：

```text
final fresh run = 20260703_231747 full20
verified_review_issue_count = 16
verified_review_issue_cluster_count = 11
critique_payload_verified_cluster_count = 0
candidate_menu_item_verified_count = 0
review_issue_candidate_critique_payload_count = 3
review_issue_candidate_deterministic_seed_count = 56
seed_topup_after_critique_failure_count = 7
mark_contested_commit_count = 9
protection = PASS
machine_gate = FAIL
```

结论：

- 审计闭环成功，旧缓存导致的 cluster 膨胀已清理。
- Critique 自主发现仍未打通；简化为 selected-menu 主输出后，MiMo 更保守，Critique-origin cluster 仍为 0。
- P32 继续阻塞。
- 下一轮应先做 Critique-only 小评估和 menu salience/supervision，而不是继续放大 full20 或放宽 verifier。
