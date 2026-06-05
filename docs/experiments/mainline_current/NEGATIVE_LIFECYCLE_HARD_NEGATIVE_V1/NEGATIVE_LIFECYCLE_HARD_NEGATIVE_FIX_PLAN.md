# NEGATIVE_LIFECYCLE_HARD_NEGATIVE_FIX_PLAN

## 总目标

当前系统的 evidence/support 层已经明显改善，但 final decision 仍受负面状态负担影响。下一轮不再调 controller，也不再粗暴放宽 accept/reject，而是解决两个剩余问题：

1. `unresolved / evidence_gap / flaw / conflict` 中哪些是真正 paper-grounded blocker，哪些只是 context/meta/targetless burden。
2. reject 样本中是否存在可证据化的 hard-negative grounding，避免只看到 positive support 就误判 accept。

## 当前已经解决的部分

- `Final Recommendation View Runtime v1` 已经打破 binary always-reject 的解释口径：`accept_like=1`，恢复 `jVEoydFOl9`，无 false accept。
- `borderline_positive` 不再映射为 accept，避免把 reject 样本中的局部 positive support 当作整篇接收依据。
- context limitation / targetless unresolved / unverified hard-negative 已经在离线 hard-negative v2/v4 中分开。

## 仍未解决的部分

### 1. Negative lifecycle burden 仍高

9B fulltest39 raw state 仍有：

- `unresolved_count=269`
- `evidence_gap_count=110`
- `flaw_count=48`
- `conflict_note_count=73`

这些不能全都当作 paper weakness，也不能全都忽略。必须按 final-view lifecycle 分类。

### 2. Hard-negative grounding 不稳定

系统能抽出 positive support，但对“为什么有 support 的 reject 仍应 reject”的 grounded blocker 还不稳定。当前 hard-negative extraction 不进入 runtime，只作为离线诊断。

### 3. Recovery 不是主增益

`patch_committed_count=1`，说明 recovery 框架可保留，但当前主线不应继续围绕 recovery controller 调参。

## 计划阶段

### Phase A：Negative Lifecycle Audit v1

新增离线脚本，读取 9B fulltest39 final state，逐条分类：

- unresolved：`context_limitation`、`targetless_open_question`、`resolved_by_real_support`、`paper_grounded_unresolved`、`unverified_hard_negative`。
- evidence gaps：`stale_gap_resolved_by_support`、`fallback_gap`、`open_gap`。
- flaws：`grounded_major_or_critical`、`ungrounded_candidate`、`fallback_or_meta_flaw`、`minor_or_nonblocking`。
- conflicts：`fallback_or_stale_conflict`、`open_conflict`。

输出 aggregate 和 case table。

### Phase B：Final-view lifecycle diagnostics

把上面的分类结果作为 final-view diagnostic，不改变 live `ReviewState`，不进入 manager routing。

目标是让 final recommendation/report 能说明：

- 为什么是 `accept_like`；
- 为什么是 `borderline_positive`；
- 为什么是 `not_assessable_uncertain`；
- 为什么是 `reject_like`。

### Phase C：Hard-negative evidence plan

只在离线层继续做 hard-negative case study，不接 runtime。若未来要增强，则必须先证明：

- reject 样本中能稳定抽出 grounded blocker；
- accept 保护样本不被误伤；
- 9B 上也稳定，而不是只在 4B 小样本上有效。

## 不做事项

- 不重启 sticky/throttle/progression gate。
- 不把 novelty/soundness/empirical 低分裸接 reject。
- 不把 `not_assessable` 映射成 accept。
- 不在 live merge 阶段做 state hygiene mutation。
- 不把 hard-negative extraction 直接接入 runtime。

## 成功标准

- 39 条样本能给出每条的 negative lifecycle 分类。
- 能量化 raw negative burden 中 context/meta/targetless/stale 的比例。
- 能找出真正 `reject_like` 的 grounded blocker 样本。
- 论文结果能解释：系统不是简单全 reject，而是在 evidence-grounded view 下区分 accept-like、borderline、not-assessable 和 reject-like。
