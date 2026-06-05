# Final-View Report Renderer v1 Decision

## 结论

建议保留为论文层 report rendering / final-view 展示模块。

本轮把 final report 的负面内容拆成 `Confirmed Weaknesses`、`Potential Concerns`、`Review Limitations`、`Unresolved Questions` 四类，避免把 candidate flaw、fallback/malformed JSON、excerpt limitation 直接写成确认论文缺陷。

## 关键数字

- reports: `39`
- reports_with_confirmed_weakness: `1`
- reports_with_potential_concerns: `6`
- reports_with_review_limitations: `35`
- reports_with_unresolved_questions: `39`
- confirmed_weakness_meta_leak_rows: `0`

## 对主试验的意义

当前最可信的系统输出不是单一 accept/reject，而是证据约束下的 final-view review。正式主试验可以继续报告 accept/reject health check，但论文主表应加入 report hygiene、criterion grounding、support quality 和 final-view recommendation。

## 下一步

下一步应整合 `Mainline-Final-v1` 主表：把 runtime evidence 指标、support quality、hard-negative lifecycle、criterion grounding、final-view report 分区放进同一份 fulltest39 分析，而不是继续新增 runtime controller。
