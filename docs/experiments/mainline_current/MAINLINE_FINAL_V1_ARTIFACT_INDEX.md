# Mainline-Final-v1 Artifact Index

## 用途

本文件只做索引，帮助后续写论文或交给外部模型分析时选对文件。当前目录中文档很多，但不是每个文件都属于最终主线。

## 当前主线结论文件

| 文件 | 用途 |
| --- | --- |
| `MAINLINE_FINAL_V1_SPEC.md` | 当前主线边界：runtime 保留、offline 保留、不进入主线的分支。 |
| `MAINLINE_FINAL_V1_PREFLIGHT_AUDIT.md` | 主试验前预检：确认旧 controller 默认关闭，并检查候选 runtime jsonl 是否混入 sticky/progression/support-formation 触发。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_PREFLIGHT.md` | clean 4B fulltest39 preflight；旧 controller runtime 触发全部为 0。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_REPORT.md` | clean 4B fulltest39 统一报告：decision/support/JSON/state/recovery/criterion。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_CASE_TABLE.md` | clean 4B fulltest39 逐样本表。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_DECISION.md` | clean 4B fulltest39 保留/下一步决策。 |
| `SUPPORT_QUALITY_FINAL_AUDIT_4B_CLEAN.md` | clean 4B support quality 最终审计；修正 ablation/table 过宽口径。 |
| `UNRESOLVED_GAP_LIFECYCLE_AUDIT.md` | clean 4B unresolved/gap lifecycle 审计。 |
| `FLAW_LIFECYCLE_FINAL_AUDIT.md` | clean 4B flaw lifecycle 审计，区分 fallback/meta、candidate 与 grounded major flaw。 |
| `FINAL_RECOMMENDATION_POLICY_SIMULATION_V2.md` | clean 4B final recommendation policy 离线模拟。 |
| `PAPER_MAIN_RESULTS_TABLE_V1.md` | 论文主表草稿，强调 final decision 是 health check，final-view recommendation 是诊断输出。 |
| `FINAL_RECOMMENDATION_POLICY_V1_FINAL.md` | 当前冻结的 final recommendation view 口径：accept/reject 只作 health check，主输出为多类 recommendation view。 |
| `FINAL_RECOMMENDATION_POLICY_V2_EXECUTION_PLAN.md` | clean 4B final recommendation v2 执行计划。 |
| `FINAL_RECOMMENDATION_POLICY_V2_FINAL.md` | V2 final-view 推荐口径：不自动产生 accept_like，support-quality positive 先归为 borderline_positive。 |
| `FINAL_RECOMMENDATION_VIEW_V2_CLEAN_4B_CASE_TABLE.md` | V2 逐样本 recommendation view 表。 |
| `FINAL_RECOMMENDATION_POLICY_V2_EXECUTION_RESULT.md` | V2 执行结果与下一步人工核查建议。 |
| `FINAL_RECOMMENDATION_CALIBRATION_V1_RESULTS.md` | 弥补 accept collapse 的离线校准结果：high precision / balanced / three-way view 对比。 |
| `FINAL_RECOMMENDATION_CALIBRATION_V1_DECISION.md` | 校准结论：high precision 作为 accept_like，balanced-only 作为 borderline_positive。 |
| `FINAL_RECOMMENDATION_CALIBRATION_CASE_REVIEW_V1.md` | 四个关键样本的校准解释：2 个 recovered accept 与 2 个 balanced false-accept risk。 |
| `MAINLINE_FINAL_V1_DRY_RUN_REPRODUCIBILITY.md` | 一键离线复现 dry-run / paper-pack 的入口，记录命令、关键指标和产物检查。 |
| `PAPER_RESULTS_NARRATIVE_V1.md` | 论文结果叙事草稿。 |
| `PAPER_CASE_STUDIES_V1.md` | 论文 case study 草稿。 |
| `PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md` | 负结果总结：sticky/throttle/live hygiene/negative blocker 等为何不作为主线。 |
| `MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md` | 基于 final-view invalid binding filter 的 failure taxonomy。 |
| `MAINLINE_FINAL_V1_CASE_STUDY_PACK.md` | recovered accept / false accept / false reject 的逐案分析入口。 |

## Runtime 保留组件证据

| 文件 | 结论 |
| --- | --- |
| `EVIDENCE_JSON_CONTRACT_V1_FULLTEST39_DECISION.md` | Evidence JSON contract 是当前保留的 runtime 修复之一。 |
| `EVIDENCE_ID_TURN_SCOPING_V1_FULLTEST39_DECISION.md` | Evidence ID turn-scoping 修复跨 turn evidence 覆盖，保留。 |
| `EVIDENCE_FALLBACK_TARGET_ISOLATION_V1_1_FULLTEST39_DECISION.md` | fallback target isolation v1.1 作为 Evidence 输入卫生基线保留。 |

## Offline / Final-View 分析证据

| 文件 | 用途 |
| --- | --- |
| `FINAL_VIEW_INVALID_BINDING_FILTER_V1_DECISION.md` | invalid-bound/fallback/unbound support 只在 final-view 过滤，不改 live state。 |
| `FINAL_VIEW_FLAW_LIFECYCLE_DECISION.md` | flaw lifecycle / meta leakage 用于 report hygiene，不进入 live state。 |
| `CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39.md` | 9B fulltest39 criterion coverage / grounding 审计。 |
| `CRITERION_GROUNDING_LINKER_V1_DECISION.md` | criterion linker 是报告 grounding 层，不是 decision rule。 |
| `SUPPORT_QUALITY_AUDIT.md` | support quality / independence 的核心审计。 |
| `EMPIRICAL_EVIDENCE_SUFFICIENCY_AUDIT_V1.md` | calibration 之后的 empirical support 充分性审计，说明下一刀应优先补 empirical/result/table support。 |
| `HARD_NEGATIVE_GROUNDING_AUDIT_V1.md` | balanced false-accept risk 的 hard-negative grounding 审计，说明不能把 balanced 直接映射为 accept。 |
| `EMPIRICAL_NEGATIVE_CASE_TABLE_V1.md` | empirical/negative grounding 逐样本 case table。 |
| `NEXT_CUT_AFTER_CALIBRATION_DECISION.md` | calibration 后下一刀决策：Empirical Evidence Targeted Audit/Pass v1。 |
| `EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_PROTOCOL.md` | empirical/result/table support 的 context/raw/payload 断点观测协议。 |
| `EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_SANITY.md` | 纯静态 sanity，验证新观测字段能落入 turn log。 |
| `EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_DECISION.md` | 保留该纯观测补丁，下一步用真实样本统计断点分布。 |
| `SERVER_IMPORT_PATH_GUARD.md` | 服务器导入路径保护，防止误导入旧 `/root/zssmas` 代码。 |

## 明确不保留的方向

| 方向 | 原因 |
| --- | --- |
| sticky / throttle / progression gate | 多轮验证显示更像后置控制器，不能解决 evidence/state 层早期问题。 |
| runtime Claim Binding Guard v1 | fulltest39 显示 live 清空 invalid `claim_id` 会压缩 accept-side support formation。 |
| live state hygiene mutation | 会改变 inference trajectory，容易压缩 positive support。 |
| final decision 阈值硬调 | 会把 support/criterion/fallback 污染误读成 accept/reject 改善。 |
| criterion-based runtime decision | 当前 criterion grounding 还不足，只能作为审计和报告层。 |

## 对外汇报建议

如果只给网页 GPT 或导师一小组文件，建议给：

1. `MAINLINE_FINAL_V1_SPEC.md`
2. `PAPER_MAIN_RESULTS_TABLE_V1.md`
3. `MAINLINE_FINAL_V1_FAILURE_TAXONOMY.md`
4. `MAINLINE_FINAL_V1_CASE_STUDY_PACK.md`
5. `PAPER_NEGATIVE_FINDINGS_SUMMARY_V1.md`

这样能避免对方只看某一轮局部结果，误以为系统目标是刷 accept/reject accuracy。

## Evidence Empirical / Clean Dry-Run Artifacts

| artifact | purpose |
| --- | --- |
| `docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_OBSERVABILITY_V1_MIXED16_4B.md` | mixed16 empirical observability distribution。 |
| `docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_STRUCTURING_V1_PROTOCOL.md` | prompt-only empirical structuring protocol。 |
| `docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_STRUCTURING_V1_COMPARE.md` | mixed16 baseline vs structuring v1 compare。 |
| `docs/experiments/mainline_current/EVIDENCE_EMPIRICAL_STRUCTURING_V1_DECISION.md` | mixed16 retain / next-step decision。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_README.md` | 根目录 clean dry-run 结果包说明。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502.jsonl` | clean 4B fulltest39 runtime jsonl，39 rows。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502.log` | clean 4B fulltest39 run log。 |
| `MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502_SUMMARY.json` | clean 4B fulltest39 unified summary。 |
