# P31.8 Critique Selection Closed-Loop Plan

日期：2026-07-03

正确工作目录：

```text
/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524
```

不要在废弃目录 `/Users/zss/Downloads/DrMAS-master` 上继续推进。

## 目标

P31.8 不追求把总 issue 数量继续做高，而是修复 P31.7 暴露的 Critique 自主发现断点：

```text
P31.7 fresh full20:
verified_review_issue_count = 16
verified_review_issue_cluster_count = 11
critique_payload_verified_cluster_count = 0
candidate_menu_item_verified_count = 0
review_issue_candidate_critique_payload_count = 3
review_issue_candidate_deterministic_seed_count = 56
protection = PASS
```

结论：strict verifier + deterministic/entity seed 路线稳定，但 Critique-origin 仍未打通。P32 继续阻塞。

## 根因

1. Critique 看到的 selector menu 仍包含容易被 verifier 打掉的低价值项，尤其是 efficiency/resource 已被 inventory 覆盖的候选。
2. 菜单选择原先强制 slot diversity，导致高风险 efficiency/reproducibility 项能挤进有限 prompt 预算。
3. runner 只把 selected `candidate_menu_id` 展开成 candidate，没有保存 prompt-time menu item 快照；后续 state/verifier 重算菜单时，如果该 id 被当前质量过滤掉，就会被记为 stale/filtered，无法区分“真实失败”与“菜单重算失配”。
4. deterministic seed top-up 会掩盖 Critique-origin 失败，所以 P31.8 的小评估必须继续保留 Critique-only / origin-separated 指标。

## 本轮代码改动

### 1. 菜单质量前置过滤

`efficiency_cost_gap` 菜单项如果目标是 runtime / latency / memory / FLOP / hardware 等资源维度，而当前 inventory anchor 已经包含资源证据，则不再展示给 Critique：

```text
rejection_reason = efficiency_cost_menu_already_observed_in_inventory
```

这针对 P31.7 中 Critique 选择的 efficiency 候选被 `missing_entity_already_observed_in_inventory` 打掉的问题。

### 2. 菜单排序改为 verifier-survival first

`_select_review_issue_candidate_menu_items` 不再先按 slot diversity 强制每槽露出一个候选，而是按现有 rank 直接选取最可能过 verifier 的候选，并保留 per-type cap。

Prompt 可见 selector menu 同步缩小：

```text
max_items = 6
max_per_type = 2
max_per_claim = 2
```

Critique 指令从“选 1-3 个”改为“选 1-2 个”，避免小模型为了凑数量硬选边缘项。

### 3. selected-menu 快照

runner 在把 `selected_menu_items` 展开成 `reviewer_negative_candidates` 时，会携带受限的 `review_issue_candidate_menu_item` 快照。

state normalizer 会保留规范化后的快照字段。bundle verifier 先查当前 menu lookup；如果 lookup 缺失但 candidate 带有同 claim / same issue type / same candidate_menu_id 的快照，则用快照恢复菜单绑定，再继续走原有严格验证。

重要边界：

```text
没有快照的 stale selected id 仍然失败。
快照不能绕过 claim anchor / inventory anchor / concrete item / counterevidence / target-quality verifier。
```

## 当前验证

已完成：

```text
py_compile:
  agent_system/environments/env_package/review/state.py
  agent_system/inference/review_runner.py
  agent_system/review_prompts.py
  agent_system/review_manager_policy.py
  tests/test_review_decision_hygiene.py

lightweight smoke assertions:
  selector prioritizes high-quality missing_ablation over low-survival slot coverage
  efficiency/resource menu item is hidden when inventory already reports resource measures
  selected-menu snapshot survives current menu lookup miss and still verifies through strict bundle path
```

`pytest` 当前不可直接运行：系统 Python、bundled Python 均未安装 pytest 模块。本轮未擅自安装依赖。

## 下一步

1. 运行 Critique-only 小样本评估，开启：

```bash
DRMAS_CRITIQUE_ONLY_DISCOVERY_EVAL=1
```

目标不是 full20，而是确认：

```text
selected_menu_item_count > 0
candidate_menu_item_verified_count > 0
critique_payload_verified_cluster_count > 0
seed_topup_after_critique_failure_count = 0
protection = PASS
```

2. 如果 Critique-only 小评估仍为 0：

```text
继续修 menu construction / salience，不跑 full20，不进 P32。
```

3. 只有 Critique-only 小评估出现稳定 verified cluster 后，再跑 fresh full20，并重新生成 dashboard / case table / recovery table / manual audit / entry gate。

## P32 Entry Gate 保持不变

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

在满足上述 gate 前，不进入 P32，不声称 Critique autonomous discovery solved。

## 20260704 Attribution-Fix 更新

后续审计发现，P31.8 stable-id smoke 中 `critique_payload_verified_cluster_count = 0`
不完全是 Critique 没选中，而是 final-view 归因丢失：

```text
Critique selected_menu item
→ runner 展开成 reviewer_negative_candidate
→ deterministic seed 先验证同一 issue cluster
→ evidence 去重保留 seed-origin record
→ Critique-origin evidence 不再单独 materialize
→ dashboard 把 Critique 计为 0 / failed
```

本次修复采用只读归因：

```text
selected-menu candidate 必须带 prompt-time menu snapshot
AND (claim_id, issue_type, normalized target) 匹配已 verified cluster
THEN 计入 critique_selected_verified_cluster_count /
     candidate_menu_item_verified_count
BUT 不新增 evidence，不改 verifier，不允许无 snapshot 的 stale/hallucinated id
```

涉及文件：

```text
agent_system/environments/env_package/review/state.py
scripts/dashboard_run_comparison_v1.py
scripts/audit_review_issue_case_table_v1.py
scripts/p31_6_entry_gate_audit.py
tests/test_review_decision_hygiene.py
```

新增关键指标：

```text
candidate_menu_item_verified_by_existing_cluster_count
critique_selected_verified_cluster_count
critique_selected_verified_by_existing_cluster_count
critique_selected_verified_clusters
```

验证：

```text
focused pytest = 5 passed
py_compile = PASS

P31_8_ATTRFIX8_20260704_132142:
  papers = 8
  verified_review_issue_count = 7
  verified_review_issue_cluster_count = 5
  critique_payload_verified_cluster_count = 3
  candidate_menu_item_verified_count = 3
  protection = PASS
  machine gate = PASS
  manual gate = REQUIRED

P31_8_ATTRFIX_FULL20_20260704_115546:
  papers = 20
  verified_review_issue_count = 22
  verified_review_issue_cluster_count = 15
  critique_payload_verified_cluster_count = 7
  critique_selected_verified_cluster_count = 7
  candidate_menu_item_verified_count = 8
  candidate_menu_item_verified_by_existing_cluster_count = 7
  mark_contested_commit_count = 9
  protection = PASS
  machine gate = PASS
  manual gate = REQUIRED
```

当前结论：

```text
P31.8 的机器侧 Critique selected-menu discovery 已经打通，不再是 0。
但这不是 paper-ready 结论，仍需要填写并验证：
  P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_TEMPLATE.md/json

P32 进入条件更新为：
  machine gate PASS
  manual audit validation PASS
  manual A/B Critique-origin clusters >= 3
  manual_D_clusters = 0 或 D 类不进入 paper-facing 主表
```

### Manual Audit Draft

已基于 case table + raw paper text 做一轮 cluster-level 初审：

```text
P31_8_ATTRFIX_FULL20_20260704_115546_MANUAL_AUDIT_FILLED_DRAFT.json

A:
  NnExMNiTHw / acceptance_prediction_head
  WpXq5n8yLb / recurrent_draft_model
  mHv6wcBb0z / generalized_noise_regularization

B:
  GE6iywJtsV / graph_control_module
  a6SntIisgg / global_encoder
  fGXyvmWpw6 / efficiency_resource_measurement

D:
  TPAj63ax4Y / zero-shot_choice_mechanism_module
```

验证结果：

```text
ALLOW_D validation:
  manual_A_B_clusters = 6
  critique_origin_manual_A_B_clusters = 6
  manual_D_clusters = 1
  status = PASS only when D is allowed/excluded from paper-facing claims

STRICT validation:
  status = FAIL
  blocker = manual_D_clusters = 1
```

下一步优先级：

```text
不要继续刷数量。
先加 counterevidence/guard：
  如果 paper text 明确写了 "ablations over this stage / zero-shot instance
  choice pipeline / selected stage"，则 selected-stage missing_ablation 不能计
  verified issue。

目标：
  删除 TPAj63ax4Y 这类 D cluster
  保留 6 个 A/B Critique-origin clusters
  strict manual gate 才能 PASS
```

### Guard Follow-Up 完成

已加入 selected-stage / zero-shot-choice ablation counterevidence guard，并重算：

```text
P31_8_ATTRFIX_GUARD_FULL20_20260704_115546_*

verified_review_issue_count = 22
verified_review_issue_cluster_count = 14
critique_payload_verified_cluster_count = 6
candidate_menu_item_verified_count = 7
protection = PASS

manual_A_clusters = 3
manual_B_clusters = 3
manual_A_B_clusters = 6
manual_D_clusters = 0
manual validation = PASS
entry gate with manual audit = PASS
```

当前结论：

```text
P31.8 guard 版是当前 P32-entry candidate。
限制：这是对已有 20260704_115546 full20 raw 的 current-code recompute，
不是 guard 后新 API full20。最终论文定稿前最好再跑一次 fresh full20 复核。
```
