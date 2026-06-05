# Final-View Flaw Lifecycle Decision v1

## 结论

`Final-View Flaw Lifecycle / Meta-Leakage Simulation v1` 值得保留为离线 derived-view 分析层，但暂时不要接入 live state，也不要作为新的 accept/reject 硬规则。

## 关键结果

- 原始 fulltest39: `predicted_accept_count=0`, `accept_recall=0.0000`, `reject_recall=1.0000`, `macro_f1=0.4348`。
- derived strict: `predicted_accept_count=16`, `accept_recall=0.2222`, `reject_recall=0.5333`, `macro_f1=0.3819`。
- derived labels: `{'accept_like': 16, 'borderline': 10, 'not_assessable': 12, 'reject_like': 1}`。
- flaw meta/artifact burden: excerpt/system/fallback/malformed 相关项大量存在，例如 `flaw_excerpt_limitation=14`, `flaw_system_meta_limitation=0`, `flaw_fallback_or_malformed_artifact=25`。

## 判断

这轮说明：当前全 reject 不应只解释为 final threshold 太严，也不应只解释为 support 数量不足。final view 里确实存在大量未验证 candidate、excerpt limitation、system/meta limitation 和 fallback/malformed artifact，它们会污染 Key Weakness 与 reject blocker。

但 derived strict 没有显著恢复 accept-like，这同样重要：即使移除 meta/excerpt/fallback 负担，gold accept 仍缺少足够的 non-abstract / empirical / independent positive support。因此下一步不应直接调 accept 阈值。

## 下一步

建议进入 `MAINLINE_FINAL_V1_SPEC + unified metrics dry run`，但必须把本层作为 final-view/report hygiene 的组成部分：

1. runtime 主线继续保持 Evidence Binding / JSON Robustness / fallback target isolation；
2. final-view 层加入 flaw lifecycle / meta-leakage 分类；
3. criterion-aware report 中把 excerpt/system/fallback artifact 放进 Review Limitations / Not Assessable，而不是 Key Weakness；
4. final decision 仍作为 health check，不作为论文唯一主指标；
5. 不恢复 Support Formation Pass，不回 sticky/throttle/gate，不做 live state hygiene mutation。
