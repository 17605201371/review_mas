# Final Recommendation Direction Decision v1

## 当前结论

当前不应继续把系统目标压成硬二分类 `accept/reject`。更合理的论文主线是：

> runtime 负责构建 evidence-grounded ReviewState；final-view 层基于 support quality、criterion grounding 和 state hygiene 输出可诊断推荐视图。

也就是说，`accept/reject` 仍然可以作为 health check，但不应成为当前唯一主指标。

## 为什么不继续做 negative blocker

`Negative Evidence Anchor Extraction v1` 说明论文正文里能抽到 table/result/baseline/ablation 等 anchor：

- 10/10 diagnostic rows 有 anchor。
- 10/10 有定量 anchor。

但 `Negative Evidence Anchor Confirmation Pass v1` 没能把这些 anchor 稳定转成有用 blocker：

- false_accept trusted blocker: `0 / 7`
- recovered_accept trusted blocker: `1 / 3`
- parse error: `0`

这说明问题不是 JSON 或锚点不可见，而是当前 4B 在 anchor-only 条件下无法稳定确认真正区分 false accept 的负向 blocker。继续强化 blocker 很可能会误伤 accept，而不是解决主问题。

## 为什么转向 support-quality filter

`Final-View Support Quality Filter v1` 显示：

| rule | pred_accept | true_accept | false_accept | accept_recall | reject_recall | macro_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sim4_current_combined | 10 | 3 | 7 | 0.3333 | 0.7667 | 0.5477 |
| sqf_two_positive_criteria | 4 | 2 | 2 | 0.2222 | 0.9333 | 0.5846 |
| sqf_high_precision | 1 | 1 | 0 | 0.1111 | 1.0 | 0.5412 |

这说明 support quality filter 可以降低 false accept，但如果直接当二分类规则，会牺牲大量 accept recall。

## 推荐视图结果

`Final Recommendation View v1` 给出更符合审稿辅助系统定位的输出：

| label | count |
| --- | ---: |
| not_assessable | 22 |
| borderline_positive | 12 |
| borderline_insufficient | 3 |
| accept_like | 1 |
| reject_like | 1 |

其中：

- `accept_like` 只有 1 条，而且 gold 是 accept，说明高精度 accept-like 是可行的。
- `borderline_positive` 混合了 4 条 accept 和 8 条 reject，说明这类样本不能强行映射为 accept。
- `not_assessable` 占多数，说明当前 final-view 最大问题是证据/维度不足，而不是简单 reject 阈值太严。
- `reject_like` 只有 1 条，说明当前系统仍缺少可靠的 paper-grounded hard negative blocker。

## 下一步方向

下一步不应做：

- sticky / throttle / progression gate；
- live state hygiene mutation；
- final decision 阈值硬调；
- 继续强造 negative blocker；
- 把 criterion 分数直接接进 runtime decision。

下一步应做：

1. 冻结 `Final Recommendation View v1` 作为论文层推荐视图。
2. 在 final report 中明确区分：
   - `accept_like`
   - `borderline_positive`
   - `borderline_insufficient`
   - `reject_like`
   - `not_assessable`
3. 论文主结果报告：
   - Evidence Binding / JSON Robustness 改善 state construction；
   - Support Quality / Criterion Grounding 改善可诊断性；
   - Final Recommendation View 避免 always-reject 和 false-accept 硬映射。
4. 若继续实验，只做小范围 `criterion-grounded report rendering + recommendation view` 集成，不再开新 controller。

## 总判断

当前系统已经不适合继续用“二分类准确率”定义成功。更准确的结论是：

> 系统已经能形成部分高精度 positive recommendation，但对许多样本仍应诚实输出 borderline 或 not-assessable；这比默认 reject 或强行 accept 更符合 evidence-grounded review assistance 的论文目标。
