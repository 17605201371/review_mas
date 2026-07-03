# P31-P34 ReviewState 执行计划

日期：2026-07-02

本文档用于把后续开发从“继续堆审稿缺陷数量”收束到一条可执行的 ReviewState 生命周期路线。当前主目标不是让 `verified_review_issue_count` 无限升高，而是在不放宽 verifier 的前提下，让系统稳定地产生、验证、去重、审计并恢复 reviewer-worthy issue clusters。

正确工作目录：

```text
/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524
```

不要继续在废弃目录 `/Users/zss/Downloads/DrMAS-master` 上推进。

## 1. 当前判断

P30 fresh full20 是当前质量基线：

```text
raw = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260701_211251.jsonl
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

结论：

- P30 是 recovery safety 和 counterevidence hygiene checkpoint，不是数量胜利。
- direct quote-grounded negative lane 继续严格，`review_negative_verified_count=0` 可以接受，不能为数字放宽。
- obligation-grounded review issue lane 已经可用，但当前 verified clusters 主要来自 deterministic seeds。
- 最大短板是 Critique payload discovery 尚未真正贡献 verified clusters。

P31 第一批代码已经把 Critique candidate menu、candidate-to-menu rebinding、origin-split metrics 和若干 safety fixes 接上。旧 P30 raw 的离线重算只能证明 plumbing 可跑，不能证明新 prompt 改善，因为旧 raw 生成时模型没看到 menu。

当前正在跑的 P31 fresh MiMo hardneg20：

```text
run tag = 20260701_234505
api_max_workers = 4
max_turns = 7
max_tokens = 1536
status at document creation = process running, jsonl currently partial
```

注意：未满 20 行前不能称为 full20。

## 2. 北极星

构建一个 evidence-grounded、stateful、auditable、recoverable 的论文审稿辅助系统。系统应维护如下生命周期：

```text
claim extraction
-> support and neutral inventory grounding
-> reviewer issue candidate discovery
-> counterevidence-first bundle verification
-> issue clustering
-> manual A/B/C/D audit
-> non-destructive recovery
-> paper-facing report
```

论文叙事应强调：

> ReviewState 管理让 LLM 审稿辅助更可审计、更可纠错，并能在保留真实正向支持的同时暴露 supported-but-contested 的审稿冲突。

不要把系统包装成自动审稿人、自动拒稿器，或自由缺陷生成器。

## 3. 全局原则

1. 优先优化 manual A/B cluster quality、recovery safety、reproducibility，而不是 raw row count。
2. deterministic seeds 必须单独报告，不能伪装成 autonomous Critique discovery。
3. direct quote-grounded negative 和 obligation-grounded review issue 必须分 lane。
4. row count、cluster count、origin split、manual A/B/C/D 必须同时报告。
5. 不为数量放宽 counterevidence、target-quality、author-limitation、retrieval-gap、fallback/context claim guard。
6. recovery 只做非破坏式 `mark_contested`，不把有真实正向支持的 claim 粗暴降级。
7. API key 不写入报告、memory 或提交内容。

## 4. P31：Critique Payload Integration

目标：让 Critique 从自由评论器变成 verifier-ready candidate selector / refiner。

验收目标：

```text
critique_payload_verified_cluster_count >= 3
critique_payload_A_B_precision >= 60%
deterministic_seed_verified_cluster_count 单独报告
protection PASS
recovery_harmful_commit_committed = 0
```

### 4.1 当前已完成

```text
review_issue_candidate_menu 已加入 Critique discovery targets
Critique prompt 已要求优先选择/copy menu item
candidate normalizer 已保留 candidate_menu_id / review_issue_slot / entity_source / discovery_origin / possible_counterevidence_terms
_reviewer_candidate_absence_gap_items 已支持 candidate-to-menu rebinding
verified bundle / evidence / materialized issue 已保留 candidate_menu_id 和 menu metadata
dashboard / case table 已增加 P31 origin-split 指标
recovery id union / generic protocol target rejection / ranch_encoder guard 已落地
```

### 4.2 立即执行

等 P31 fresh run 完成后生成：

```text
P31_FRESH_API4_234505_HARDNEG20_DASHBOARD.md/json
P31_FRESH_API4_234505_HARDNEG20_AUDIT.json
P31_FRESH_API4_234505_REVIEW_ISSUE_CASE_TABLE.md/json
P31_FRESH_API4_234505_RECOVERY_CASE_TABLE.md/json
P31_FRESH_API4_234505_MANUAL_CLUSTER_AUDIT.md/json
```

必须检查：

```text
jsonl line count = 20
protection PASS
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
recovery_harmful_commit_committed = 0
verified_review_issue_count
verified_review_issue_cluster_count
critique_payload_gap_count
critique_payload_menu_bound_count
critique_payload_verified_count
critique_payload_verified_cluster_count
candidate_menu_item_count
candidate_menu_item_used_count
candidate_menu_item_verified_count
mark_contested_commit_count
verified_issue_cluster_without_recovery_count
```

### 4.3 决策分支

如果 P31 fresh 达成：

```text
critique_payload_verified_cluster_count >= 3
protection PASS
manual A/B quality 不退化
```

则进入 P32 可复现性阶段。

如果 P31 fresh 仍然是：

```text
critique_payload_verified_cluster_count = 0
```

则不要继续追总数量。下一步改 Critique 输入结构：

- 给 Critique 更短、更明确的 candidate menu。
- 每个 claim 限制 top-K menu items，避免 prompt 膨胀。
- 每个 menu item 加 `why_review_worthy` 和 `counterevidence_aliases`。
- 让 Critique 输出“选择/拒绝 menu item”的结构化判断，而不是自由生成缺陷。
- 将 deterministic seed verifier 定位为当前可靠能力，把 autonomous Critique discovery 写成未完成瓶颈或后续贡献。

## 5. P31.5：Manual Audit 固化

目标：把人工审计从临时判断变成可复用 artifact。

审计单位：

```text
deduplicated issue cluster
```

标签：

```text
A = strong real review issue, paper-facing
B = defensible concern, usable with caveat
C = weak / diagnosis-pending
D = false positive / not review-worthy
MERGE = duplicate cluster merged into another cluster
```

每个 cluster 必须记录：

```text
paper_id
issue_type
normalized_missing_target
claim_anchor
inventory_anchor
counterevidence_summary
discovery_origin
manual_label
manual_label_reason
fix_needed_if_D
```

P31 hardneg20 目标：

```text
manual strict A/B clusters >= 6
D clusters <= 3
每个 D reason 映射到 regression test / prompt fix / verifier fix
```

## 6. P32：Clean Reproducibility Runs

目标：证明系统不是单次 run 偶然有效。

运行计划：

```text
3 个 clean hardneg20 runs
same code commit
code_dirty = clean
MiMo API_MAX_WORKERS=4，出问题再降级
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
deterministic_seed cluster recurrence
harmful recovery count across all runs
```

验收：

```text
harmful recovery = 0 across all runs
D rate <= 20-25%
manual strict A/B count 方差可解释
存在 recurring A/B clusters
```

## 7. P33：Full39 主实验

前提：

```text
P31 protection PASS
P31/P32 manual audit protocol 稳定
D-class regression guards 已补
Critique-origin 至少有可解释结果，或明确作为局限报告
```

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
- deterministic seed origin 和 Critique payload origin 分开报。
- row count 和 cluster count 分开报。
- 不隐藏 `review_negative_verified_count=0`，把它作为 strict direct quote lane 的 caveat。

## 8. P34：Paper-Ready Benchmark

目标：把开发 checkpoint 变成论文可引用 benchmark。

需要产物：

```text
manual annotated issue cluster dataset
baseline comparisons
system ablations
multi-run stability analysis
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

## 9. 风险与应对

### Critique 仍然没有 verified clusters

应对：

- 不放宽 verifier。
- 缩短 menu，提升 menu item 质量。
- 把 Critique 改成 menu selector，而不是缺陷生成器。
- 论文中明确 deterministic seed verifier 是当前可靠主能力。

### Prompt 过长导致 MiMo 变慢

应对：

- 每个 claim 限 top-K menu items。
- dashboard 增加 prompt length / latency 统计。
- 优先传 structured menu summary，不传长篇解释。

### Issue 数量回升但 D 类增多

应对：

- 不以 row count 作为主指标。
- 每个 D 类必须进入 regression list。
- case table 必须显示 target quality、counterevidence reason、discovery origin。

### Recovery 看起来数量高但不全是 verified issue repair

应对：

- dashboard 分开报 `verified_review_issue_repair`、`stale_absence_repair`、`effective_repair_without_verified_negative`。
- 论文只把 verified issue repair 写成主结果。

## 10. 最近 7 步执行顺序

```text
1. 等当前 P31 fresh MiMo run 结束；确认 jsonl = 20 行。
2. 生成 P31 fresh dashboard、audit、review issue case table、recovery case table。
3. 做 P31 manual cluster audit，重点分 seed-origin / critique-origin。
4. 更新 memory.md，写清 P31 结果、限制和下一步。
5. 若 Critique-origin 达标，进入 P32 clean reproducibility runs。
6. 若 Critique-origin 仍为 0，先改 Critique menu selector 结构，不追数量。
7. P32 稳定后再进入 Full39 和 paper-ready benchmark。
```

## 11. 论文表述边界

可以写：

```text
DrMAS verifies reviewer-worthy issue bundles rather than merely generating review prose.
It distinguishes copied quote-grounded negatives from obligation-grounded claim/inventory mismatches,
filters candidates through counterevidence-first guards,
clusters issue rows into auditable units,
and uses non-destructive recovery to preserve supported-but-contested claims.
```

不能写：

```text
系统能自动审稿。
row count 等于独立真实缺陷数。
deterministic seed 主导时 autonomous Critique discovery 已成功。
为了数量淡化 review_negative_verified_count=0。
没有 manual A/B cluster audit 就宣称缺陷数量充分。
```

## 12. 当前 P31 执行结果更新

状态：P31 fresh MiMo API4 full20 已完成，结果是部分成功。

运行时修复：

```text
旧 run 20260701_234505 在 4/20 后卡住，XyB4VvF01X 本地 CPU 99%。
根因是 final-view/dashboard metrics 重跑 menu/gap/verifier/regex-heavy report path。
已修为 cached hygiene + lightweight funnel/report metrics。
```

Authoritative run：

```text
mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_004622.jsonl
P31_FRESH_API4_004622_HARDNEG20_DASHBOARD.md/json
P31_FRESH_API4_004622_REVIEW_ISSUE_CASE_TABLE.md/json
P31_FRESH_API4_004622_RECOVERY_CASE_TABLE.md/json
P31_FRESH_API4_004622_MANUAL_CLUSTER_AUDIT_20260702.md/json
```

结果：

```text
protection PASS
verified_review_issue_count = 19
verified_review_issue_cluster_count = 14
manual A/B clusters = 8
critique_payload_verified_cluster_count = 1
deterministic_seed_verified_cluster_count = 13
review_negative_verified_count = 0
mark_contested_commit_count = 9
recovery_case_verified_review_issue_repair = 8
recovery_harmful_commit_committed = 0
```

结论：

```text
P31 未达到 critique_payload_verified_cluster_count >= 3。
不能进入 P32 前假设 Critique discovery 已解决。
下一步应做 Critique-as-menu-selector，而不是继续提高 deterministic seed 数量。
```
