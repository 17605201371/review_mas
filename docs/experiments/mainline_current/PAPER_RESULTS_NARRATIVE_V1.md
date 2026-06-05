# Paper Results Narrative v1

## 结果段落主线

当前结果应围绕“从黑箱二分类转向可诊断审稿辅助”来写，而不是围绕 accuracy 刷分。

## Result 1：Runtime final decision collapses under binary recommendation

### 中文草稿

在 `Mainline-Final-v1` 的 fulltest39 预跑中，runtime final decision 仍然输出 `39/39 reject`。这说明传统 accept/reject 层仍存在明显 collapse，不能作为系统能力的唯一指标。我们因此将 runtime final decision 作为 health check，而不是主输出。

### 应配表格

- `PAPER_MAIN_RESULTS_TABLE_V1.md` 中 Runtime Health 部分。

## Result 2：Support provenance matters for paper-review state

### 中文草稿

系统的 raw ReviewState 中仍存在 `13` 条 fallback-bound strong support，全部来自 abstract 并绑定到 `claim-fallback-1`。但这些信号没有进入 `accept_like`，说明 final-view 层已经能将 raw diagnostic support 与 decision-eligible real-claim support 分离。

### 应配表格

- `MAINLINE_FINAL_V1_METRIC_CONSISTENCY_AUDIT.md`
- `SUPPORT_PROVENANCE_RECONCILIATION_V1.md`

## Result 3：Support-quality filters expose a precision-recall trade-off

### 中文草稿

更严格的 support-quality filter 可以显著降低 false accept。高精度规则将 false accept 降到 `0`，但只恢复 `1` 个 true accept；较均衡规则恢复 `2` 个 true accept，同时仍有 `2` 个 false accept。这说明 support quality 是必要诊断信号，但不适合直接作为硬二分类规则。

### 应配表格

- `FINAL_VIEW_SUPPORT_QUALITY_FILTER_V1_SIMULATION.md`

## Result 4：Negative blocker formation remains unreliable

### 中文草稿

我们进一步尝试从正文 anchor 中确认 negative blocker。虽然 anchor extraction 能覆盖全部 diagnostic 样本，并且每个样本都有定量 anchor，但 anchor-only confirmation 并没有在 false accept 样本中形成 trusted blocker，反而误伤一个 recovered accept。这说明当前系统不应把 negative blocker formation 接入 final decision。

### 应配表格

- `NEGATIVE_EVIDENCE_ANCHOR_CONFIRMATION_PASS_V1_COMPARE.md`

## Result 5：Final Recommendation View provides a better output interface

### 中文草稿

最终我们将输出改写为多类 final-view recommendation：`accept_like`、`borderline_positive`、`borderline_insufficient`、`reject_like` 和 `not_assessable`。该视图只给出 `1` 个高精度 `accept_like`，同时保留 `12` 个 `borderline_positive` 和 `22` 个 `not_assessable`。这比默认 reject 或强行 accept 更符合 evidence-grounded review assistance 的定位。

### 应配表格

- `FINAL_RECOMMENDATION_REPORT_V1_AUDIT.md`
- `PAPER_CASE_STUDIES_V1.md`

## Discussion 重点

1. 系统不是 reviewer replacement，而是 stateful diagnostic assistant。
2. 多类 recommendation view 是更诚实的输出接口。
3. 当前主要限制是 negative blocker formation 和 empirical support formation 仍不足。
4. 后置 controller 不能替代 evidence/state 质量。

## Limitation 重点

1. fulltest39 仍是预跑，不是正式大规模实验。
2. `accept_like` 高精度但低召回。
3. `not_assessable` 占多数，说明证据可见性和 grounding 仍需改进。
4. raw state 仍有 fallback 残留，需要在论文中明确解释 provenance separation。
