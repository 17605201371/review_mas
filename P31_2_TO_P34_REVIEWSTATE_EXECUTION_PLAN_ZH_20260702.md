# P31.2 -> P34 ReviewState 执行计划

日期：2026-07-02

状态：当前 authoritative 计划文档。后续除非另开 P32/P33 文档，本文件作为 P31.2 继续推进、P32 clean reproducibility、P33 full39、P34 paper-ready benchmark 的执行准绳。

正确工作目录：

```text
/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524
```

不要继续使用废弃目录：

```text
/Users/zss/Downloads/DrMAS-master
```

## 1. 当前结论

后续目标不应继续定义为“把审稿缺陷数量做高”。P28-P31 已经说明，单纯追数量会重新带来三类风险：

- counterevidence miss：论文已有反证/补充实验，但系统仍把缺口算成 verified issue。
- 模板化缺陷：把普通 encoder、decoder、module、训练动作包装成 missing ablation。
- deterministic seed 膨胀：系统看起来发现了很多 issue，但实际主要是规则 seed + verifier，不是 Critique 自主发现。

当前更合理的北极星是：

> 构建一个 evidence-grounded、stateful、auditable、recoverable 的审稿辅助系统，稳定维护 review issue 的生命周期：候选发现 -> 证据/反证核查 -> cluster 去重 -> 人工 A/B/C/D 审计 -> 非破坏性 recovery -> paper-facing 报告。

论文叙事应强调 ReviewState 管理、obligation/inventory mismatch verification、counterevidence-first guard 和 non-destructive recovery。不要把系统包装成自动拒稿器或自由缺陷生成器。

## 2. 当前 checkpoint

P31.2 authoritative current-code fresh full20：

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_105402.jsonl
dashboard = P31_2_FRESH_API4_105402_HARDNEG20_DASHBOARD.md/json
review issue cases = P31_2_FRESH_API4_105402_REVIEW_ISSUE_CASE_TABLE.md/json
recovery cases = P31_2_FRESH_API4_105402_RECOVERY_CASE_TABLE.md/json
papers = 20/20
protection = PASS
evidence_json_fallback_rate_pct = 0
critique_prompt_chars_median = 11668
critique_prompt_chars_max = 11673
critique_prompt_over_15k_turns = 0
critique_prompt_over_30k_turns = 0
verified_review_issue_count = 12
verified_review_issue_cluster_count = 10
review_negative_verified_count = 1
mark_contested_commit_count = 5
review_issue_candidate_critique_payload_count = 19
candidate_menu_item_used_count = 7
candidate_menu_item_verified_count = 0
critique_payload_verified_cluster_count = 1
deterministic_seed_verified_cluster_count = 8
manual audit artifact = P31_2_FRESH_API4_105402_MANUAL_CLUSTER_AUDIT_20260702.md/json
manual A/B clusters = 5
manual C clusters = 3
manual D clusters = 2
selector failure audit = P31_3_SELECTOR_FAILURE_AUDIT_20260702.md
```

解释：

- `020210`、`093950`、`100316` 都只能作为 partial/diagnostic，不再作为 current-code full20 依据。
- `105402` 证明 P31.2 的运行时阻塞已经解除：MiMo API4 full20 跑完，JSON fallback 为 0，Critique prompt 没有超过 15k。
- `105402` 也证明 Critique-as-menu-selector 尚未达标：Critique 使用了 7 个 menu item，但 `candidate_menu_item_verified_count=0`；最终 verified clusters 仍主要来自 deterministic seeds。
- 初步 case-table manual audit 显示 10 个 system clusters 里约 5 个 A/B，不能把 10 直接写成真实缺陷数。
- P31.3 selector failure audit 已定位 menu-used-but-not-verified 的主因：prompt-time menu id 与后处理重算 lookup 不稳定，exact id miss 后 fuzzy fallback 可误绑到其他 menu item，且部分 menu item 本身请求已被 inventory 覆盖的证据。
- 下一阶段不应继续先追数量，而应实现 P31.3 selector-quality/rebinding patch，同时把 2 个 D 类问题写成 guard/test。
- P31.3 第一补丁已完成：exact `candidate_menu_id` miss 不再 fuzzy-bind，候选 copied menu id 会作为 `critique_payload_menu_metadata` 保留，colliding `obligation_id` 不能靠泛词重叠注入 unrelated expected entity。
- P31.3 第二补丁已完成：Critique payload dedupe 改为包含 `candidate_menu_id` / normalized target；generic `quantitative/result/metric table for ...` insufficient-evaluation menu items 被 prompt 前过滤；105402 selector probe 显示 bad result-table/analyze-mechanism menu items 为 0。

P31.2 prompt/runtime 修复进展：

```text
offline prompt diagnosis source = P31_FRESH_API4_004622 raw
before compaction worst Critique prompt ~= 183k chars
first compaction worst Critique prompt ~= 34k chars
second compaction rendered Critique prompt median/max = 10074 chars
fresh API run 105402 Critique prompt median/max = 11668/11673 chars
long review_issue_discovery_targets leak = 0
selector-menu rows in offline check = 17/20
empty inventory observations in offline check = 0
focused pytest = 6 passed
py_compile = passed on touched files
fresh API run = 20/20, protection PASS
```

已完成的关键修复：

- Critique discovery mode 下不再同时暴露完整 `review_issue_discovery_targets` 和 selector/summary，避免重复输入。
- `Critique State Slice` 改为暴露 compact `review_issue_discovery_target_summary`，并标记完整 targets 被省略。
- selector menu capped：每个 claim 最多 2 个，每轮最多 4 个高质量候选。
- target evidence / negative evidence candidates / flaw candidates 改为 compact prompt view，`recovery_hydration` 在 discovery mode 下省略。
- runner 记录 `worker_prompt_char_counts`，turn log 持久化 `critique_prompt_chars` / `evidence_prompt_chars` / `claim_prompt_chars`。
- `REVIEW_ISSUE_DISCOVERY_PROMPT` 改成 5910 字符的 menu-first 短合同，保留 concrete entity、inventory anchor、counterevidence terms、retrieval-gap ban 和 slot schema。
- compact prompt state 会在 runtime state 未持久化 `evaluation_inventory` 时从 evidence/paper text 派生短 inventory，避免 selector menu recall 依赖手动注入 inventory。
- dashboard 增加 Critique worker turns、prompt chars median/max、`critique_prompt_over_15k_turns`、`critique_prompt_over_30k_turns`。

剩余风险：

- Critique payload discovery 仍弱：`critique_payload_verified_cluster_count=1`，未达到 P31 目标 `>=3`。
- Menu uptake 有了但没有转化：`candidate_menu_item_used_count=7`，`candidate_menu_item_verified_count=0`。
- 当前 10 个 clusters 已有初步 case-table audit，但还需要 full-paper audit；不能直接作为 paper-ready true issue count。
- D 类问题包括：`analyze_the_mechanism` 这类 action/related-work phrase 被当成 ablation target，以及 `held-out_coverage_for_ripu` 这类 baseline-name scope target。
- 若后续继续优化，应优先解释 menu item 为什么没过 verifier，而不是放宽 verifier 或增加 deterministic seeds。

## 3. 全局原则

1. 不放宽 verifier 换数量。
2. direct quote-grounded negative lane 和 obligation-grounded review issue lane 保持分离。
3. deterministic seed、Critique payload、menu-bound candidate、claim-obligation fallback 必须分开报告。
4. 主报告使用 cluster count 和 manual A/B/C/D，不使用 row count 夸大效果。
5. recovery 只做非破坏式 `mark_contested`，不把有真实正向支持的 claim 粗暴 downgrade。
6. retrieval/context/truncated-material gap、author self-limitation、generic “more evaluation” 不进入 verified issue。
7. 每个 D 类 false positive 都必须回写为 regression test、prompt guard 或 verifier guard。
8. API key 不写入计划、日志摘要、memory 或提交说明。

## 4. P31.2-A：运行时阻塞处理

目标：让 P31.2 fresh full20 能稳定跑完，否则后续指标没有意义。

状态：105402 current-code fresh full20 已完成，本项视为 P31.2 已验证通过。

### 4.1 诊断

立即确认：

```text
process still alive?
jsonl line count still increasing?
log 是否还有 API request/response?
CPU hot path 是否集中在 regex/state audit/report finalization?
Critique prompt_chars 是否仍出现 19k 级别膨胀?
```

当前已知症状：

```text
旧 run jsonl 卡在 12/20
进程 CPU 约 100%
旧日志显示 Critique prompt 可到 19k+，离线复现发现最坏可到 183k
sample 曾显示 `_sre` regex search/substitution 热点
```

### 4.2 修复方向

两批 prompt/runtime 修复已做，但 fresh full20 尚未验证。若 fresh run 仍出现运行时或 prompt 问题，再做以下低风险修复：

- 进一步压缩 observation 中的 Critique State Slice，目标保持 median 8k-12k、hard ceiling 15k。
- 保留 menu-first、concrete entity、inventory anchor、counterevidence terms、retrieval-gap ban、slot schema；不要恢复重复解释和长规则堆叠。
- 若 selector menu 缺失，优先修 inventory/source ranking，而不是扩大 menu 数量。
- 给 Critique prompt 增加 hard cap 指标：
  - `critique_prompt_chars_max`
  - `critique_prompt_chars_median`
  - `critique_prompt_over_15k_turns`
  - `critique_prompt_over_30k_turns`
- 定位 regex-heavy finalization path，优先加缓存或短路：
  - 对重复 quote/text normalization 缓存结果；
  - 对 paper_text 全文 regex 搜索加长度/次数限制；
  - 对 case table/dashboard 离线计算避免在 runner 热路径重复执行。
- 给 hardneg20 run 明确 partial/full 标记，未满 20 行不得更新 canonical full20 指针。

### 4.3 验收

```text
fresh hardneg20 reaches 20/20
no >30 min no-progress CPU spin
Critique prompt max chars <= 15k preferred, <= 30k hard ceiling
candidate menu still present on most papers
protection PASS
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

105402 结果：

```text
fresh hardneg20 = 20/20
critique_prompt_chars_max = 11673
critique_prompt_over_15k_turns = 0
protection = PASS
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

## 5. P31.2-B：Critique-as-Menu-Selector

目标：让 Critique 从自由评论器变成 verifier-ready candidate selector/refiner。

状态：部分达成。105402 中 `candidate_menu_item_used_count=7`，说明 Critique 确实开始使用 selector menu；但 `candidate_menu_item_verified_count=0`、`critique_payload_verified_cluster_count=1`，说明 menu-bound candidate 到 verifier 的链路仍未打通。

### 5.1 代码方向

- 每篇 paper 生成紧凑 selector menu：
  - menu id 使用短 id；
  - 每个 claim 最多 2-4 个 menu item；
  - 每个 item 有 `issue_type`、`expected_entity`、`why_review_worthy`、`inventory_anchor`、`counterevidence_aliases`。
- Critique prompt 改成 select/reject 优先：
  - 先复制 `candidate_menu_id`；
  - 可以 reject menu item，并说明 counterevidence 或 target 不成立；
  - free-form candidate 只能补充，且必须给 claim anchor、inventory anchor、counterevidence terms。
- normalizer/rebinding：
  - exact `candidate_menu_id` 优先；
  - 缺 id 时用 claim_id + issue_type + expected_entity token overlap 回绑；
  - 回绑只能补 metadata，不能绕过 verifier。
- dashboard/case table：
  - `candidate_menu_item_used_count`
  - `candidate_menu_item_verified_count`
  - `critique_payload_menu_bound_count`
  - `critique_payload_verified_cluster_count`
  - `deterministic_seed_verified_cluster_count`

### 5.2 验收

```text
critique_payload_verified_cluster_count >= 3
candidate_menu_item_used_count >= 3
critique_payload A/B precision >= 60%
manual strict A/B clusters >= 6
D clusters <= 3
protection PASS
recovery_harmful_commit_committed = 0
```

如果 Critique-origin 仍然只有 0-1 个 verified cluster，不进入 P32；应继续做 P31.3 selector-quality/rebinding，而不是继续压 prompt 或增加 seed 数量。

P31.3 具体问题清单：

- 对 7 个 used menu items 建 failure table：是否死于 no inventory、no selected requirement、generic item、counterevidence、off-claim、target quality、normalization/rebinding。
- 对每个 failure 判断是 menu item 本身不该出现，还是 Critique 输出丢字段，还是 rebinding 没复制 menu metadata。
- 若 menu item 质量差，改 menu ranking/source；若 Critique 丢 id，进一步简化 select-only schema；若 rebinding 丢 metadata，修 `_reviewer_candidate_absence_gap_items` 的 menu copy path。
- 不允许任何改动绕过 claim anchor、inventory anchor、target-quality、counterevidence、author-limitation/retrieval-gap guard。

## 6. P31.5：Manual Audit 固化

目标：把人工审计从临时判断变成稳定 artifact。

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

每个 cluster 记录：

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

验收：

```text
hardneg20 manual strict A/B clusters >= 6
D clusters <= 3
每个 D reason 都有对应 regression test 或 guard 计划
```

## 7. P32：Clean Reproducibility Runs

前提：

```text
P31.2 full20 稳定跑完
protection PASS
Critique-origin 有可解释改善，或明确记录为未解决短板
manual audit protocol 已固定
```

运行计划：

```text
3 个 clean hardneg20 runs
same code commit
code_dirty = clean
MiMo API_MAX_WORKERS = 4，失败再降回 2
max_turns = 7
max_tokens = 1536
api_max_retries = 8
api_timeout = 600
```

报告：

```text
manual strict A/B cluster count mean/std/min/max
D cluster rate
cluster Jaccard overlap
same-paper issue recurrence
same-target entity recurrence
critique_payload cluster recurrence
deterministic_seed cluster recurrence
harmful recovery count across all runs
verified issue repair coverage
```

验收：

```text
harmful recovery = 0 across all runs
D rate <= 20-25%
manual strict A/B count 方差可解释
存在 recurring A/B clusters
```

## 8. P33：Full39 主实验

前提：

```text
P31/P32 protection PASS
D-class regression guards 已补
manual audit protocol 稳定
运行时稳定，不再出现 12/20 长时间 CPU spin
```

Full39 目标：

```text
manual strict A/B clusters >= 12-15
manual permissive A/B clusters >= 16-20
D rate <= 20%
non-ablation A/B clusters >= 30%
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
negative_grounding_conflict_count = 0
```

必须按类型报告：

```text
missing_ablation
missing_baseline / weak baseline
scope / robustness / generalization mismatch
protocol / reproducibility gap
efficiency / resource gap
result-claim mismatch
direct quote-grounded negative
```

如果 non-ablation A/B clusters 不足 30%，下一轮优先补 slot-specific entity/inventory extraction，而不是放宽 verifier。

## 9. P34：Paper-Ready Benchmark

目标：把系统结果变成论文可用 benchmark。

需要产物：

```text
manual labeled cluster dataset
baseline comparison
ablation study
multi-run stability report
case studies
failure taxonomy
```

建议 baseline：

```text
single-agent review generation
multi-agent without ReviewState
without counterevidence guard
without cluster guard
without recovery bridge
deterministic seed only
Critique payload only
```

论文主问题：

```text
ReviewState 是否提升审计性？
counterevidence-first guard 是否提升 precision？
non-destructive recovery 是否安全保存 supported-but-contested claim？
Critique discovery 在结构化 menu 帮助下能否贡献独立 A/B clusters？
```

## 10. 立即执行清单

1. 继续验证 P31.3 selector-quality patch：
   - 已完成：exact `candidate_menu_id` 查不到时，不允许 fuzzy-bind 到另一个 menu item；
   - 已完成：候选自带 copied menu id 可进入 gap/bundle path；
   - 已完成：colliding `obligation_id` 不能靠 generic target token 注入 unrelated expected entity；
   - 已完成：同 claim/type/requirement 的不同 selected menu target 不再互相 dedupe 掉；
   - 已完成：过滤 generic `quantitative/result/metric table for ...` insufficient-evaluation menu item；
   - 已完成：增加 action/related-work ablation target guard；
   - 待做：baseline-name-as-scope-target guard 仍需继续加强；
   - 不放宽 verifier。
2. 跑 fresh MiMo hardneg20：
   - `API_MAX_WORKERS=4`
   - `max_turns=7`
   - `max_tokens=1536`
   - 未满 20 行不叫 full20。
3. 根据结果决定：
   - Critique-origin 达标且 manual A/B 不退化 -> 进入 P32 clean reproducibility。
   - Critique-origin 未达标 -> 继续 P31.3 selector/prompt 输入修复，不进入 P32。
