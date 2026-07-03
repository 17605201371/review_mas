# P31-P34 ReviewState 中长期计划

日期：2026-07-02

正确工作目录：

```text
/Users/zss/Downloads/zssmas-codex-p26-optimization-20260524
```

不要在废弃目录 `/Users/zss/Downloads/DrMAS-master` 上继续推进。

## 1. 总目标

后续目标不应继续定义为“把 issue 数量做高”。P29/P30/P31 已经证明：单纯追数量会重新带来 counterevidence miss、模板化 missing-ablation、deterministic seed 膨胀和 row-level duplicate inflation。

中长期目标应改为：

> 构建一个 evidence-grounded、stateful、auditable、recoverable 的论文审稿辅助系统，能够稳定维护 review issue 生命周期：候选发现 -> 证据/反证核查 -> cluster 去重 -> 人工 A/B/C/D 审计 -> 非破坏性 recovery -> paper-facing 报告。

论文叙事不应是“AI 自动审稿”或“系统自动判拒稿”，而应是：

> ReviewState 管理让 LLM 审稿辅助更可审计、更可纠错；系统能保留真实正向支持，同时以 obligation/inventory mismatch 的形式暴露 supported-but-contested 的审稿冲突。

## 2. 当前 checkpoint

当前 authoritative P31 fresh run：

```text
run = mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_004622.jsonl
dashboard = P31_FRESH_API4_004622_HARDNEG20_DASHBOARD.md/json
review issue cases = P31_FRESH_API4_004622_REVIEW_ISSUE_CASE_TABLE.md/json
recovery cases = P31_FRESH_API4_004622_RECOVERY_CASE_TABLE.md/json
manual audit = P31_FRESH_API4_004622_MANUAL_CLUSTER_AUDIT_20260702.md/json
```

核心结果：

```text
protection_passed = True
review_negative_verified_count = 0
verified_review_issue_count = 19
verified_review_issue_cluster_count = 14
manual A/B clusters = 8
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

当前判断：

- P31 是部分成功：review issue lane、cluster、recovery bridge 和保护线已经能跑通。
- P31 没有达成 Critique discovery 目标：`critique_payload_verified_cluster_count=1`，低于目标 `>=3`。
- 不能把 14 个 clusters 叙述成 Critique 自主发现能力；当前仍然是 deterministic seed verifier 主导。
- direct quote-grounded negative lane 继续为 0 可以接受，不能为了数字放宽负向 quote verifier。
- P31.1 已补两个代码修正：theory/loss-analysis missing-ablation guard、Critique prompt 更强 menu id copy contract；但这些修正后还没有 fresh MiMo rerun。

## 3. 全局原则

1. 优化 manual A/B cluster quality、recovery safety、reproducibility，而不是 raw row count。
2. direct quote-grounded negative 和 obligation-grounded review issue 必须分 lane。
3. deterministic seed、Critique payload、claim-obligation fallback、direct quote origin 必须分开报告。
4. row count、cluster count、manual A/B/C/D、origin split 必须同时报告。
5. 不为数量放宽 counterevidence、target-quality、author-limitation、retrieval-gap、fallback/context claim guards。
6. Recovery 只做非破坏式 `mark_contested`，不把有真实正向支持的 claim 粗暴 downgrade。
7. 每个 D 类 false positive 都应转成 regression test、prompt guard 或 verifier guard。
8. API key 只保留在环境文件中，不写入计划、memory、dashboard 或提交说明。

## 4. P31.2：Critique-as-Menu-Selector

### 目标

把 Critique 从“自由缺陷生成器”改成“候选菜单选择器和轻量重写器”。当前系统的可靠能力是 deterministic seed + strict verifier；下一步要验证 Critique 能否在结构化菜单帮助下贡献真实 reviewer-worthy clusters。

### 代码方向

1. 生成更短的 top-K candidate menu：
   - 每个 claim 只给最强的 2-4 个 menu item；
   - menu id 更短、更容易复制；
   - menu item 必须包含 `why_review_worthy`、`expected_entity`、`inventory_anchor`、`counterevidence_aliases`；
   - generic target 不进入 menu。

2. 修改 Critique prompt 为显式 select/reject：
   - 每个 slot 先选择一个 `candidate_menu_id` 或明确 `reject_all_menu_items`；
   - 选择 menu item 时必须原样复制 `candidate_menu_id`；
   - free-form candidate 只能作为补充，并必须给出 claim anchor、observed inventory anchor、possible counterevidence terms；
   - 禁止把 “provided excerpt/current context/truncated material 缺失” 包装成论文缺陷。

3. 改 normalizer / rebinding：
   - menu id 精确命中优先；
   - 若 menu id 缺失，再用 claim_id + issue_type + expected_entity token overlap 回绑；
   - 回绑只能补充 metadata，不能绕过 verifier。

4. 降低 prompt 长度：
   - 不把长篇解释塞给 Critique；
   - 用 compact menu summary；
   - dashboard 记录 Critique prompt chars、payload valid count、menu copied count。

### 验收线

```text
protection PASS
critique_payload_verified_cluster_count >= 3
critique_payload A/B precision >= 60%
candidate_menu_item_used_count >= 3
manual strict A/B clusters >= 6
D clusters <= 3
recovery_harmful_commit_committed = 0
negative_evidence_unlinked_to_flaw = 0
positive_or_neutral_negative_candidate_count = 0
```

### 失败分支

如果 Critique-origin 仍然只有 0-1 个 verified cluster：

- 不继续追总数量；
- 把当前能力写成 deterministic-seed verifier + partial Critique integration；
- 继续缩短 menu、强化 select/reject 输出；
- 不进入 P32/P33 之前声称 autonomous Critique discovery 已解决。

## 5. P32：Clean Reproducibility Runs

### 前提

P31.2 达到至少一个可解释 Critique-origin 改善，且 protection 不退化。

### 运行设计

```text
3 个 clean hardneg20 runs
same code commit
code_dirty = clean
MiMo API_MAX_WORKERS = 4，出错再降回 2
max_turns = 7
max_tokens = 1536
api_max_retries = 8
api_timeout = 600
同一套 dashboard / case table / recovery table / manual audit pipeline
```

### 报告指标

```text
manual strict A/B cluster count mean/std/min/max
manual permissive A/B cluster count
D cluster rate
cluster Jaccard overlap
same-paper issue recurrence
same-target entity recurrence
critique_payload cluster recurrence
deterministic_seed cluster recurrence
harmful recovery count across all runs
verified issue repair coverage
```

### 验收线

```text
harmful recovery = 0 across all runs
D rate <= 20-25%
manual strict A/B clusters 方差可解释
存在 recurring A/B clusters
critique_payload clusters 单独报告，不和 deterministic seed 混报
```

P32 的目标不是每轮数量更高，而是证明结果不是单次 API 随机产物。

## 6. P33：Full39 主实验

### 前提

```text
P31/P32 protection PASS
manual audit protocol 固化
D-class regression guards 已补
Critique-origin 有可解释结果，或明确作为局限报告
```

### Full39 目标

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

### 类型多样性要求

不能只证明系统会找 missing ablation。Full39 报告必须分类型：

```text
missing_ablation
missing_baseline / weak baseline
scope / robustness / generalization mismatch
protocol / reproducibility gap
efficiency / resource gap
result-claim mismatch
direct quote-grounded negative
```

如果 non-ablation A/B clusters 不足 30%，下一步优先补 entity/inventory extraction 和 slot-specific candidate quality，而不是放宽 verifier。

## 7. P34：Paper-Ready Benchmark

### 产物

```text
manual annotated issue cluster dataset
baseline comparisons
system ablations
multi-run stability analysis
case studies
recovery safety analysis
paper-facing report templates
```

### 标注集 schema

```json
{
  "paper_id": "...",
  "cluster_id": "...",
  "issue_type": "...",
  "normalized_missing_target": "...",
  "claim_anchor": "...",
  "inventory_anchor": "...",
  "counterevidence_summary": "...",
  "discovery_origin": "critique_payload|deterministic_seed|direct_quote|claim_obligation_fallback",
  "manual_label": "A|B|C|D|MERGE",
  "manual_label_reason": "...",
  "expected_recovery": "mark_contested|diagnosis_pending|none"
}
```

### Baseline / ablation 对比

候选对比：

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
3. non-destructive recovery 是否能安全保留 supported-but-contested 冲突？
4. Critique payload 是否能贡献 deterministic seeds 之外的 reviewer-worthy issues？

## 8. 近期执行顺序

### Step 1：确认 P31.1 后是否 fresh rerun

P31.1 已经修了 theory/loss-analysis guard 和 Critique menu id copy contract，但未 rerun。下一步建议先跑一次 fresh hardneg20：

```bash
DRMAS_NEG_QUOTE_HYGIENE=1 \
DRMAS_TARGETED_NEGATIVE_SEARCH=1 \
DRMAS_FREEFORM_REVIEWER_NEGATIVE=1 \
DRMAS_REVIEW_ISSUE_BUNDLE=1 \
API_MAX_WORKERS=4 \
API_MAX_RETRIES=8 \
API_TIMEOUT=600 \
MAX_TOKENS=1536 \
bash run_hardneg20_guard3.sh
```

观察：

```text
candidate_menu_item_used_count
critique_payload_verified_cluster_count
protection_passed
manual A/B clusters
7Dub7UXTXN simulated-loss D cluster 是否消失
```

### Step 2：如果 Critique 仍弱，做 P31.2 menu selector

不要在 Critique-origin 仍为 0-1 时进入 full39 主实验。先实现短 menu、select/reject 输出、menu id preservation tests。

### Step 3：P31.2 fresh full20 + manual audit

生成：

```text
P31_2_FRESH_API4_*_HARDNEG20_DASHBOARD.md/json
P31_2_FRESH_API4_*_REVIEW_ISSUE_CASE_TABLE.md/json
P31_2_FRESH_API4_*_RECOVERY_CASE_TABLE.md/json
P31_2_FRESH_API4_*_MANUAL_CLUSTER_AUDIT.md/json
```

### Step 4：达标后进入 P32 多 run

只在 P31.2 达到 Critique-origin 和 quality 验收线后做 3-run reproducibility。

### Step 5：P32 稳定后进入 Full39

Full39 前必须确认 manual audit 标准、case table 字段和 dashboard 指标已经固定。

## 9. 论文表述边界

可以写：

```text
系统验证 reviewer-worthy issue bundles，而不是只生成 review prose。
系统区分 copied quote-grounded negatives 与 obligation-grounded claim/inventory mismatches。
系统通过 counterevidence-first guards 过滤候选。
系统把 issue rows 聚类成可审计单位。
系统用 non-destructive recovery 保存 supported-but-contested claims。
```

不能写：

```text
系统能自动审稿。
row count 等于独立真实缺陷数。
deterministic seed 主导时 autonomous Critique discovery 已成功。
为了数量淡化 review_negative_verified_count=0。
没有 manual A/B cluster audit 就宣称缺陷数量充分。
```

## 10. 最终里程碑

### M1：P31.2 Critique Discovery Checkpoint

```text
critique_payload_verified_cluster_count >= 3
candidate_menu_item_used_count >= 3
manual strict A/B clusters >= 6
D clusters <= 3
protection PASS
harmful recovery = 0
```

### M2：P32 Reproducibility Checkpoint

```text
3 clean hardneg20 runs
manual A/B count 方差可解释
D rate <= 20-25%
recurring A/B clusters 可见
harmful recovery = 0 across runs
```

### M3：P33 Full39 Evaluation

```text
manual strict A/B clusters >= 12-15
manual permissive A/B clusters >= 16-20
D rate <= 20%
non-ablation A/B clusters >= 30%
harmful recovery = 0
```

### M4：P34 Paper-Ready Benchmark

```text
人工标注集
baseline 对比
system ablation
multi-run stability
case studies
recovery safety proof
```

这条路线的核心是：先把 ReviewState 生命周期跑稳，再扩大样本和论文实验。不要再用 verifier 放松来换数量。
