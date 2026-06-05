# Mainline-Final-v1 Clean 4B Fulltest39 Decision

## 结论
- dry_run_baseline_retained: `True`
- go_for_formal_main_experiment: `False`
- recommendation: 保留为干净 4B dry-run 基线；正式主试验前继续做 recommendation policy / support-quality / hard-negative grounding 的离线收口。

## 理由
- 旧 controller 触发为 0，clean pipeline 口径已经可用于 dry run。
- fallback strong support 为 0，Evidence Binding 成果没有回退。
- 真实 accept 仍未被 runtime final decision 恢复，accept/reject 不能作为正式主指标。

## 禁止回退方向
- 不回 sticky / throttle / progression gate。
- 不做 live state hygiene mutation。
- 不用强 support 数量直接硬调 accept/reject。
