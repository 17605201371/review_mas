# MAIN_RESULTS_TABLE_9B_FULLTEST39

## 9B Fulltest39 主结果表

来源：`mainline_final_v1_closure_9b_fulltest39_20260504`。这是当前最新封版 pipeline rerun，不是新 controller 实验。

| group | metric | value | interpretation |
| --- | --- | --- | --- |
| Decision Health | row_count | 39 | 39 条 fulltest |
| Decision Health | gold_accept/gold_reject | 8 / 31 | 当前 gold inference 口径；与旧 9/30 口径有差异，论文表需固定 label source |
| Decision Health | runtime predicted accept/reject | 1 / 38 | binary decision 只作 health check |
| Decision Health | accuracy | 0.8205 | 受 reject skew 影响，不是主指标 |
| Decision Health | macro_f1 | 0.5604 | binary health check |
| Decision Health | accept_recall / reject_recall | 0.125 / 1.0 | 保守恢复 1 个 accept，无 false accept |
| Final-view Recommendation | view_counts | {'borderline_insufficient': 24, 'not_assessable_uncertain': 11, 'borderline_positive': 2, 'reject_like': 1, 'accept_like': 1} | 论文主推荐层 |
| Final-view Recommendation | accept_like / false_accept | 1 / 0 | accept_like 为 jVEoydFOl9，false accept 为 0 |
| Support Quality | real_strong_support_total | 49 | 强支持已绑定真实 claim |
| Support Quality | nonabstract_strong_support_total | 49 | 非摘要支持形成稳定 |
| Support Quality | empirical_strong_support_total | 36 | 经验/结果支持形成稳定 |
| Support Quality | fallback_strong_support_total | 0 | fallback strong 污染为 0 |
| Criterion | coverage | 39 / 39 / 39 / 39 / 39 | novelty/significance/soundness/empirical/clarity 覆盖 |
| Criterion | grounding | 39 / 38 / 36 / 33 / 39 | criterion grounding 已审计，unsupported/meta leakage 为 0 |
| Negative Lifecycle | raw unresolved/gap/flaw/conflict | 269 / 110 / 48 / 73 | raw negative burden 高，但不能直接当 paper defect |
| Negative Lifecycle | hygiene open unresolved / gap | 0 / 52 | final-view 已过滤 context/meta/stale burden |
| Recovery | patch emitted/committed | 96 / 1 | recovery 框架可运行，但非主增益 |
| Hard Negative | status_counts | {'unverified_blocker_candidate': 37, 'grounded_blocker_found': 1, 'context_limited_no_grounded_blocker': 1} | 稳定 hard-negative blocker 仍弱，是 limitation 而非新 controller 方向 |
| Hard Negative | false_accept_risk / accept_protect | 20 / 4 | 解释为什么不能硬接 support count |

## 解释

这张表支持当前论文主线：系统已经改善 evidence binding、support formation、criterion report 和 final-view hygiene；binary final decision 有轻微恢复但仍不能作为主指标。正式论文应强调 evidence-aligned recommendation view，而不是二分类准确率。
