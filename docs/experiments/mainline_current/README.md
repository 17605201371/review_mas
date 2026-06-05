# Mainline Current Artifacts

本目录收纳从根目录整理下来的主线实验文档、审计结果、配置快照和轻量 JSON 汇总。

## 当前主线

- 基线：`p25.1 + explicit recovery phase`
- 保留的 runtime 修复：Evidence Binding Robustness、Evidence JSON Contract / Robustness、Evidence fallback target isolation v1.1、Evidence ID Turn-Scoping v1。
- 保留的 offline/final-view 分析：final-view hygiene、support quality / independence、criterion coverage / grounding、criterion-grounded report section、invalid binding filter、failure taxonomy。
- 当前不应继续的方向：sticky / throttle / progression gate 的控制器叠加、criterion-based decision rule、runtime Claim Binding Guard、live-state hygiene mutation。

## 文档组织

- `CRITERION_*`：审稿维度覆盖与 grounding 的离线审计。
- `CRITERION_AWARE_FINAL_REPORT_*`：最终报告中加入 criterion section 的协议、预览、运行对比和决策。
- `DECISION_HYGIENE_*`：final-view hygiene 的离线模拟和 fulltest 对比。
- `EVIDENCE_*`：Evidence Context / Evidence Binding / Evidence JSON robustness 相关实验。
- `FINAL_VIEW_INVALID_BINDING_FILTER_*`：invalid-bound / fallback-bound / unbound support 的离线过滤与 case table。
- `MAINLINE_FINAL_V1_*`：主线 spec、统一结果表、9B/4B dry run、case study 和 failure taxonomy。
- `SUPPORT_*`：support quality、evidence independence、support criterion 联合审计。
- `FULLTEST_*`：full-test hygiene simulation 结果。
- `P25_1_RUN_CONFIG_*`：baseline/candidate 运行配置快照。

## 使用原则

根目录只保留项目入口、当前记忆和主线计划。本目录作为论文实验材料和结果追踪归档，不直接参与 runtime。

## 读数注意

本目录包含 4B retained bundle、9B fulltest39 rerun、4B ID-scoped fulltest39 等多个口径。写论文或给外部分析时，不要把不同口径的数值合并成一个“最终结果”。优先引用 `MAINLINE_FINAL_V1_SPEC.md`、`PAPER_MAIN_RESULTS_TABLE_V1.md`、`MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md` 和对应 case table，并在正文标注数据源。
