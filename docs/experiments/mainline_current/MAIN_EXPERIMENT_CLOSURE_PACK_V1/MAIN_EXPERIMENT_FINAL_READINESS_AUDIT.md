# MAIN_EXPERIMENT_FINAL_READINESS_AUDIT

## 总判断

当前可以进入论文主试验收口 / dry-run 结果整理；不建议继续 runtime 机制研发。最新 9B closure rerun 已完成，并且比旧 clean baseline 多恢复 1 个 `accept_like`，无 false accept。

## 已解决项

- Evidence Binding：`fallback_strong_support_total=0`，support 绑定污染已基本压住。
- Evidence Support：`real_strong=49`、`nonabstract=49`、`empirical=36`。
- Final-view recommendation：`accept_like=1`，`false_accept=0`，binary projection 保守。
- Criterion report：五个审稿维度 39/39 均覆盖，unsupported criterion critique 与 meta leakage 均为 0。
- 旧 controller：不再作为主线贡献，已从论文主线排除。

## 未解决但已收束的风险

- Runtime binary decision 仍偏 reject：`predicted_accept=1`，所以 binary decision 只作为 health check。
- Hard-negative grounding 弱：`grounded_blocker_found=1`，多数 blocker 仍是 unverified candidate。
- Open gaps 仍存在：`hygiene_gap_total=52`，需要作为 limitation / future work。
- Recovery commit 率低：`patch_committed=1`，recovery 是结构化过程指标，不是当前主增益。
- Gold label 口径需在论文中冻结：这轮 postprocess 为 `8 accept / 31 reject`，旧表曾使用 `9 / 30`。

## 是否阻止主试验

不阻止主试验收口，但阻止把 binary accept/reject accuracy 当论文主结果。主试验应汇报：support quality、binding precision、criterion grounding、final-view recommendation、negative lifecycle 和 recovery funnel。
