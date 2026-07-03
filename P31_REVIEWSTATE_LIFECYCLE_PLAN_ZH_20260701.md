# P31-P34 ReviewState 生命周期推进计划

日期：2026-07-01

这份计划基于 P30 fresh full20 结果、最近的代码审计，以及 GPT 网页给出的中长期建议。核心判断是：后续目标不应该继续单纯追求 `verified_review_issue_count` 数量，而应把系统推进成一条稳定、可复现、可审计、可恢复的 ReviewState 生命周期。

## 1. 北极星目标

构建一个 evidence-grounded、stateful、auditable、recoverable 的论文审稿辅助系统。系统要服务论文叙事：

```text
claim extraction
-> support / inventory grounding
-> reviewer issue candidate discovery
-> counterevidence-first bundle verification
-> issue clustering
-> manual A/B/C/D audit
-> non-destructive recovery
-> paper-facing report
```

不要把系统叙述成自动审稿人、拒稿分类器，或自由缺陷生成器。论文主张应是：

> 结构化 ReviewState 可以让 LLM 审稿辅助更可审计、更可纠错，并能在保留真实正向支持的同时暴露 supported-but-contested 的审稿冲突。

## 2. 当前 P30 状态判断

当前 authoritative checkpoint：

- Raw run：`mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260701_211251.jsonl`
- Dashboard：`P30_FRESH_API4_211251_HARDNEG20_DASHBOARD.md/json`
- Review issue case table：`P30_FRESH_API4_211251_REVIEW_ISSUE_CASE_TABLE.md/json`
- Recovery case table：`P30_FRESH_API4_211251_RECOVERY_CASE_TABLE.md/json`

关键结果：

```text
verified_review_issue_count = 13
verified_review_issue_cluster_count = 12
review_negative_verified_count = 0
mark_contested_commit_count = 8
recovery_case_verified_review_issue_repair = 8
recovery_harmful_commit_committed = 0
evidence_json_fallback_rate_pct = 0
reviewer_candidate_review_issue_critique_payload_count = 0
reviewer_candidate_review_issue_deterministic_seed_count = 13
```

解释：

- P30 是质量和 recovery safety checkpoint，不是数量胜利。
- 直接 quote-grounded negative lane 仍严格，`review_negative_verified_count=0` 不能强行刷高。
- obligation-grounded review issue lane 已经能产出少量可信 issue。
- recovery bridge 表现好：支持证据没有被破坏，系统用 `mark_contested` 保存冲突。
- 最大短板是 Critique payload discovery 没有真正接入 verifier-ready 路径，当前 verified issue 仍由 deterministic seeds 主导。

## 3. 后续总原则

1. 优先优化人工 A/B cluster 质量、recovery safety、可复现性，而不是 row count。
2. direct quote-grounded negative evidence 保持严格，不为了数字放宽。
3. deterministic seeds 要单独报告，不能伪装成 autonomous Critique discovery。
4. dashboard 同时报 row count、cluster count、origin split、manual A/B/C/D。
5. 不放宽 counterevidence、target quality、author limitation、retrieval gap、fallback/context claim guard。
6. recovery 只做非破坏式 `mark_contested`，不把有真实正向支持的 claim 粗暴降级。

## 4. P31：Critique Payload Integration

目标：把 Critique 从自由评论生成器，改造成 verifier-ready candidate selector / refiner。

验收目标：

```text
critique_payload_verified_cluster_count >= 3
critique_payload_A_B_precision >= 60%
deterministic_seed 和 critique_payload origin 分开报告
protection PASS
recovery_harmful_commit_committed = 0
```

### 4.1 增加 verifier-ready candidate menu

给 Critique 暴露 `review_issue_candidate_menu_for_claim`。每个 menu item 是候选假设，不是证据：

```json
{
  "candidate_menu_id": "menu-claim-2-missing-ablation-acceptance-head",
  "claim_id": "claim-2",
  "obligation_id": "obligation-claim-2-missing-ablation-acceptance-head",
  "issue_type": "missing_ablation",
  "required_evidence_type": "ablation_or_component",
  "expected_entity": "acceptance prediction head",
  "entity_source": "method_component",
  "inventory_id": "paper-inventory-7",
  "inventory_quote": "copied table/list/experiment anchor",
  "inventory_locator": "Table 4",
  "inventory_type": "ablation",
  "target_quality_hint": "high|medium|reject",
  "counterevidence_search_terms": ["acceptance head", "prediction head", "ablation"]
}
```

规则：

- menu item 必须来自现有 obligation / inventory substrate。
- 必须有 locatable inventory quote/list/table anchor，或可信 verified support inventory anchor。
- 泛化词如 `component`、`module`、`encoder`、`decoder`、`network`、`protocol details`、`stronger baseline` 默认不能进 menu。
- menu item 不绕过 verifier，只是帮助 Critique 生成可验证候选。

### 4.2 更新 Critique prompt contract

Critique 输出候选时优先选择 menu item，并复制：

```text
candidate_menu_id
obligation_id
claim_id
issue_type
required_evidence_type
expected_entity
observed_inventory
possible_counterevidence_terms
```

自由候选仍允许，但必须同时满足：

- 绑定真实 claim；
- 命名 concrete entity；
- 有 locatable observed inventory anchor；
- 不能把 retrieval/context/truncated material 说成论文缺陷；
- 每个 candidate 给出 counterevidence search terms。

### 4.3 Candidate-to-menu rebinding

在 `_reviewer_candidate_absence_gap_items` 加绑定逻辑：

```text
IF candidate has candidate_menu_id
OR candidate matches menu item by claim_id + issue_type + expected_entity tokens
THEN copy menu requirement, expected_entity, inventory anchor, obligation_id
AND set discovery_origin = critique_payload_menu_bound
AND run the same strict bundle verifier
```

这只是入口变宽，不是验证变松。仍必须经过：

- claim anchor locatability；
- observed inventory verification；
- missing-ablation target-quality guard；
- full-text counterevidence；
- review-worthiness guard；
- author limitation / retrieval-gap guard。

### 4.4 Safe introduced-requirement path

P30 的一个损耗点是：Critique 提出 narrower issue，但 broad requirement 已被某条 support 满足，于是 candidate 被 `no_selected_requirement` 阻断。

P31 可以允许 narrower issue 进入 bundle verification，但只在以下条件同时满足时：

```text
real claim
concrete missing/mismatch entity
locatable observed inventory
expectation auditable from paper surface / claim surface / menu item
full-text counterevidence does not resolve it
not author limitation / not retrieval gap / not generic gap
```

这不是放松 verifier，而是修复“合理 narrow issue 没入口”的问题。

### 4.5 Origin-split metrics

dashboard 和 case table 增加：

```text
critique_payload_candidate_count
critique_payload_gap_count
critique_payload_menu_bound_count
critique_payload_bundle_built_count
critique_payload_verified_count
critique_payload_verified_cluster_count
critique_payload_rejected_by_reason
deterministic_seed_candidate_count
deterministic_seed_verified_cluster_count
candidate_menu_item_count
candidate_menu_item_used_count
candidate_menu_item_verified_count
```

case table 增加：

```text
discovery_origin
candidate_menu_id
obligation_id
expected_entity
inventory_anchor_type
counterevidence_reason
review_worthiness_reason
manual_label
manual_label_reason
```

### 4.6 P31 同步安全修复

必须和 P31 一起修：

1. recovery downgrade-to-contested 检查 evidence id 时，必须同时看 `supporting_evidence_ids`、`negative_evidence_ids`、`evidence_ids`。
2. 拒绝泛化 protocol target，如 `explicit evaluation protocol details for protocol`。
3. 对泛化 protocol issue，显式 train/test split、label budget、training setup、same-setting protocol quote 应算 counterevidence。
4. 拒绝 malformed missing-ablation target，如 `ranch_encoder`。
5. `global encoder` 这类普通结构词只有明确 contribution-bound 且 inventory-bound 时才能进入 verified issue。

### 4.7 P31 测试与验收

单元测试：

- `candidate_menu_id` 能绑定 menu obligation 和 inventory。
- menu-bound Critique candidate 只有通过 strict verifier 才能 verified。
- free-form Critique candidate 没有 locatable inventory 时只能 diagnosis-pending。
- broad requirement 已满足时，narrower concrete issue 仍可进入验证入口。
- counterevidence 能挡住 stale / already-covered issue。
- generic protocol target 被拒。
- malformed ablation target 被拒。
- destructive downgrade patch 引用 issue evidence 时被重建为 `mark_contested`。

离线重算：

```text
source raw = P30 fresh full20 20260701_211251
protection PASS
critique_payload_gap_count > 0
critique_payload_verified_cluster_count > 0
no obvious D-class false-positive regression
```

fresh MiMo full20：

```text
max_turns=7
api_max_workers=4
api_max_retries=8
api_timeout=600
max_tokens=1536
```

验收：

```text
protection PASS
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
critique_payload_verified_cluster_count >= 3
manual strict A/B clusters >= 6
D clusters <= 3 if possible
```

## 5. P31.5：人工审计规范固化

目标：把 manual audit 从临时口头判断变成可复用 artifact。

产物：

```text
P31_MANUAL_CLUSTER_AUDIT_YYYYMMDD.md
P31_MANUAL_CLUSTER_AUDIT_YYYYMMDD.json
```

审计单位：

- deduplicated issue cluster，而不是 raw row。

标签：

```text
A = strong real review issue, paper-facing
B = defensible concern, usable with caveat
C = weak or diagnosis-pending
D = false positive or not review-worthy
MERGE = duplicate cluster merged into another cluster
```

目标：

```text
hardneg20 strict A/B clusters >= 6
D clusters <= 3
每个 D 类都有明确 reason
每个 D reason 映射到 regression test / prompt fix / verifier fix
```

## 6. P32：可复现性 runs

目标：不再依赖单次 clean full20。评估系统稳定性。

运行计划：

```text
3 个 clean hardneg20 runs
same code commit
code_dirty = clean
MiMo API4，除非 API 不稳定再降级
同一套 dashboard / case / recovery / manual audit pipeline
```

报告指标：

```text
manual strict A/B cluster count mean/std/min/max
D cluster rate
cluster Jaccard overlap
same-paper issue recurrence
same-target entity recurrence
critique_payload cluster recurrence
harmful recovery count across all runs
```

验收：

```text
harmful recovery = 0 across all runs
D rate <= 20-25%
manual strict A/B count stable enough to report
有可复现 recurring A/B clusters
```

## 7. P33：Full39 主实验

前提：

- P31 至少有部分 Critique-origin verified clusters；
- P31/P32 protection PASS；
- manual audit protocol 稳定；
- D-class regression guards 已加。

Full39 目标：

```text
manual strict A/B clusters >= 12-15
permissive A/B clusters >= 16-20
D rate <= 20%
non-ablation A/B clusters >= 30%
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

报告要求：

- direct quote-grounded negative 和 obligation-grounded review issue 分开报。
- seed-origin 和 Critique-origin clusters 分开报。
- 不隐藏 `review_negative_verified_count=0`，把它作为 strict direct quote lane 的 caveat。

## 8. P34：论文级 benchmark

目标：把系统从开发 checkpoint 推进到 paper-ready benchmark。

需要组件：

```text
manual annotated issue cluster dataset
baseline comparisons
system ablations
multi-run stability
case studies
recovery safety analysis
```

候选 baseline：

```text
single-agent free-form review generation
multi-agent without ReviewState
ReviewState without counterevidence guard
ReviewState without cluster guard
ReviewState without non-destructive recovery
deterministic-seed-only
Critique-payload-only
```

要回答的问题：

1. ReviewState 是否提高审计性？
2. counterevidence-first verification 是否提高 precision？
3. non-destructive recovery 是否能保存 supported-but-contested 冲突？
4. Critique payload discovery 是否能提供 deterministic seeds 之外的 reviewer-worthy issues？

## 9. 论文叙事边界

可以写：

- 系统区分 direct quote-grounded negative 与 obligation-grounded review issue。
- 系统通过 claim anchor、observed inventory、concrete missing/mismatch entity、counterevidence check 验证非 quote 型审稿缺陷。
- 系统保留正向支持，同时用 contested relation 暴露冲突。
- P30/P31 展示的是 recovery safety 和 ReviewState hygiene，不是自动拒稿能力。

不能写：

- 系统是 autonomous reviewer。
- row count 等于独立真实缺陷数。
- deterministic seeds 主导时宣称 autonomous Critique discovery 已成功。
- 为了数量淡化 `review_negative_verified_count=0`。
- 没有 manual A/B cluster audit 就声称缺陷数量充分。

推荐表述：

```text
DrMAS verifies reviewer-worthy issue bundles rather than merely generating review prose. It distinguishes copied quote-grounded negatives from obligation-grounded claim/inventory mismatches, filters candidates through counterevidence-first guards, clusters issue rows into auditable units, and uses non-destructive recovery to preserve supported-but-contested claims.
```

## 10. 最近执行顺序

下一批实现建议：

```text
1. 完成 P31 candidate menu generation 与 Critique prompt contract。
2. 完成 candidate-to-menu rebinding 和 origin-split funnel metrics。
3. 修 recovery id union、generic protocol rejection、malformed ablation rejection。
4. 补 focused unit tests。
5. 用 P30 fresh raw 做 offline recompute。
6. offline sane 后跑 clean MiMo API4 hardneg20 full20。
7. 生成 dashboard、review issue case table、recovery table、manual cluster audit。
```

P31 决策点：

```text
IF critique_payload_verified_cluster_count >= 3
AND protection PASS
AND manual A/B quality does not regress
THEN proceed to P32 reproducibility runs.

IF Critique payload still verifies 0 clusters
THEN do not chase quantity.
Treat deterministic seed verifier as current capability,
and either redesign Critique input more deeply or frame Critique discovery as future work.
```

## 11. 2026-07-01 实现检查点

本轮已完成 P31 第一批代码闭环：

- `review_issue_candidate_menu` 已加入 Critique discovery targets。
- Critique prompt 已要求优先选择/copy menu item，并返回 `candidate_menu_id`、`obligation_id`、inventory anchor、counterevidence terms。
- candidate normalizer 已保留 `candidate_menu_id`、`review_issue_slot`、`entity_source`、`discovery_origin`、`possible_counterevidence_terms`。
- `_reviewer_candidate_absence_gap_items` 已支持 explicit id 或 claim/type/entity token match 的 candidate-to-menu rebinding，并把命中项标成 `critique_payload_menu_bound`。
- verified bundle / evidence / materialized review issue 已保留 `candidate_menu_id` 和 menu metadata。
- dashboard 和 case table 已增加 P31 origin-split 指标与 `candidate menu id` 列。
- safety fixes 已落地：recovery id union、generic protocol target rejection、`ranch_encoder` malformed ablation rejection。

验证状态：

```text
py_compile: touched runtime files / scripts / tests 全通过
pytest: 当前本机 Python 环境无 pytest，未能直接运行
direct Python assertions: normalizer、menu-bound verification、protocol guard、ranch_encoder guard、recovery id union 均通过
offline P30 raw recompute: P31_MENU_RECOMPUTE_211251_* 生成成功，protection PASS
```

P30 raw 离线重算结果：

```text
verified_review_issue_count = 12
verified_review_issue_cluster_count = 11
review_issue_candidate_critique_payload_count = 31
critique_payload_gap_count = 18
critique_payload_menu_bound_count = 5
critique_payload_verified_count = 0
critique_payload_verified_cluster_count = 0
candidate_menu_item_count = 98
candidate_menu_item_used_count = 0
candidate_menu_item_verified_count = 0
```

解释：

- 这证明 P31 plumbing 和 metrics 已能在旧 raw 上运行。
- 旧 P30 raw 不能证明 Critique prompt 改善，因为那轮模型输出时还没有看到 `review_issue_candidate_menu`。
- 下一步必须跑 fresh MiMo hardneg20，并生成 dashboard、review issue case table、recovery table、manual cluster audit，才能判断 P31 是否真正让 Critique-origin verified clusters 从 0 提升。

## 12. 2026-07-02 Fresh Run 检查点

P31 fresh MiMo API4 hardneg20 已完成，但结论是“部分成功”，不是 P31 完成。

### 12.1 运行时热点修复

第一次 fresh run `20260701_234505` 在 `4/20` 后卡住。第二批里 `XyB4VvF01X` 的 API 调用已经结束，但 Python 进程持续 99% CPU，无新日志。采样显示主要耗在 Python regex/string 处理。

修复：

- `_review_issue_candidate_funnel_metrics` 改成轻量观测路径，不再在 final-view 里重跑 candidate menu lookup、gap construction、paper inventory search、review-worthiness 或 full-text counterevidence。
- dashboard / case / recovery 脚本优先读取 run 里缓存的 `decision_hygiene` 或 `state_audit.decision_hygiene`。
- dashboard 的 cluster-origin metrics 改成读缓存的 verified bundle/direct-negative 标签，不再调用 state verifier 重扫 `evidence_map`。
- review issue case table 使用缓存的 `review_issue_bundle_items` 作为 authoritative row filter，避免当前代码离线重验导致 row count 和 dashboard 不一致。

验证：

```text
py_compile 通过
P30 raw dashboard/case/recovery 到 /tmp 生成快速完成
旧卡住样本 XyB4VvF01X 在新 run 中正常完成
```

### 12.2 Authoritative fresh run

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_004622.jsonl
dashboard = P31_FRESH_API4_004622_HARDNEG20_DASHBOARD.md/json
review issue case table = P31_FRESH_API4_004622_REVIEW_ISSUE_CASE_TABLE.md/json
recovery case table = P31_FRESH_API4_004622_RECOVERY_CASE_TABLE.md/json
manual audit = P31_FRESH_API4_004622_MANUAL_CLUSTER_AUDIT_20260702.md/json
```

核心指标：

```text
protection = PASS
review_negative_verified_count = 0
verified_review_issue_count = 19
verified_review_issue_cluster_count = 14
reviewer_candidate_review_issue_critique_payload_count = 1
reviewer_candidate_review_issue_deterministic_seed_count = 18
critique_payload_verified_count = 1
critique_payload_verified_cluster_count = 1
deterministic_seed_verified_cluster_count = 13
candidate_menu_item_count = 3
candidate_menu_item_used_count = 0
candidate_menu_item_verified_count = 3
mark_contested_commit_count = 9
recovery_case_verified_review_issue_repair = 8
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

人工初审：

```text
system rows = 19
system clusters = 14
manual A clusters = 3
manual B clusters = 5
manual A/B clusters = 8
manual C clusters = 4
manual D clusters = 1
manual MERGE clusters = 1
critique-origin A/B clusters = 1
```

### 12.3 决策

- P31 把 Critique-origin verified cluster 从 `0` 提到 `1`，同时保持 protection PASS 和 non-destructive recovery。
- P31 没达到 roadmap 目标 `critique_payload_verified_cluster_count >= 3`，不能把 autonomous Critique discovery 写成已解决。
- 当前能力表述应是：系统能稳定验证 obligation-grounded issue bundles；Critique payload 开始接入但仍弱，deterministic seeds 仍主导。
- 下一步不要追总数量，应该做 Critique-as-menu-selector：短 top-K menu、显式 select/reject、强制复制 `candidate_menu_id`、为每个 menu item 给 same-setting / counterevidence aliases。
- 需要新增一个 precision guard：防止把 theory/loss-analysis claim 包装成 empirical missing-ablation issue。触发案例是 `7Dub7UXTXN` 的 `simulated_loss` D-class cluster。

### 12.4 后续代码修复

fresh audit 后已补两处 P31.1 修复：

```text
1. missing-ablation target quality 新增 theory/loss-analysis guard。
   `component-isolation ablation for simulated loss` 这类 target，如果上下文是 learning dynamics /
   global minimum / expressivity / theorem / proof，而不是 empirical benchmark/performance，就拒绝。

2. Critique prompt 的 menu contract 加强。
   只要候选来自 review_issue_candidate_menu，就必须精确复制 candidate_menu_id。
   如果不用 candidate_menu_id 走 free-form candidate，rationale 必须说明为什么没有合适 menu item，
   并提供自己的 copied observed_inventory anchor。
```

验证：

```text
py_compile 通过 state.py / review_prompts.py / tests/test_review_decision_hygiene.py
direct focused tests 通过：
- theory/loss target quality guard
- existing theory-anchor review issue rejection
```

尚未验证：

```text
这些后续代码还没有重新跑 fresh MiMo。
下一轮 fresh run 应重点看 candidate_menu_item_used_count 是否 > 0，
以及 critique_payload_verified_cluster_count 是否从 1 继续接近 P31 目标 3。
```
