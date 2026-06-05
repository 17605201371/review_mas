# NEGATIVE_LIFECYCLE_HARD_NEGATIVE_DECISION_V1

## 结论

本轮确认：当前未解决的主要问题不是 evidence/support 不形成，而是 raw negative burden 的生命周期没有被论文口径解释清楚。通过 final-view negative lifecycle audit，raw negative 项被拆成了更可解释的类别。

## 9B fulltest39 审计结果

输入：`outputs/results_main/review_infer/mainline_final_v1_9b_context_v2_2_fulltest39_merged_gold_20260503.jsonl`

| metric | raw | final-view hygiene |
| --- | ---: | ---: |
| unresolved | 269 | 0 open unresolved |
| evidence gaps | 110 | 52 open gaps |
| conflicts | 73 | 35 open conflicts |
| flaws | 48 | 1 grounded major/critical flaw |

### Unresolved 分类

| category | count |
| --- | ---: |
| context_limitation | 69 |
| targetless_open_question | 200 |

解释：raw unresolved 主要不是 paper-grounded blocker，而是上下文限制和 targetless open question。因此不能直接作为 reject 依据。

### Evidence gap 分类

| category | count |
| --- | ---: |
| stale_gap_resolved_by_support | 42 |
| open_gap | 68 |

解释：42 个 gap 已被 real support 解决，应从 final-view negative burden 中移除；52 个 final-view open gap 是后续 support/context 质量仍需改善的主要来源。

### Flaw 分类

| category | count |
| --- | ---: |
| fallback_or_meta_flaw | 43 |
| ungrounded_candidate | 4 |
| grounded_major_or_critical | 1 |

解释：真正能作为 hard-negative blocker 的只有 1 个 grounded major/critical flaw。大多数 flaw 是 fallback/meta 或 ungrounded candidate，不能强触发 reject。

### Conflict 分类

| category | count |
| --- | ---: |
| fallback_or_context_conflict | 53 |
| open_conflict | 20 |

解释：大多数 conflict 是 fallback/context 派生，不能裸接 final decision。

## 已解决什么

1. raw unresolved 不再等同 paper weakness。
2. stale evidence gap 能在 final-view 里识别。
3. fallback/meta flaw 不再作为 confirmed weakness。
4. final recommendation view 现在返回 open gap、stale gap、context/meta uncertainty、targetless uncertainty 等诊断字段。
5. binary final decision 仍为保守投影，只有 strict `accept_like` 映射为 accept。

## 仍未解决什么

1. `open_gap=52` 说明仍有不少 claim 没有形成足够直接的支持。
2. `open_conflict=20` 说明还有部分状态冲突需要更好 evidence/claim reconciliation。
3. hard-negative grounding 仍弱：真正 grounded blocker 只有 1 个，reject 样本中“为什么拒”的证据化解释还不够。

## 下一步

不建议继续调 final decision 阈值。下一步如果继续优化，应做两件事之一：

1. `Open Gap Resolution Audit v1`：检查 52 个 final-view open gap 是否真缺 evidence，还是 target/evidence binding 没关联上。
2. `Hard-Negative Grounding Case Study v1`：针对 reject 样本中 high support 的 false-risk case，人工/离线定位缺失的 grounded blocker。

当前不应重启 sticky/throttle/progression gate，也不应把 hard-negative extraction 直接接入 runtime。

## 本轮追加修复

`Flaw flaw-X lacks anchored evidence.` 这类 gap 已从 final-view evidence gaps 中移除。它们属于 flaw lifecycle 诊断，而不是 claim evidence gap。修复后 final-view open gaps 从 `68` 降到 `52`，recommendation 分布保持 `accept_like=1` 且 `false_accept=0`。
