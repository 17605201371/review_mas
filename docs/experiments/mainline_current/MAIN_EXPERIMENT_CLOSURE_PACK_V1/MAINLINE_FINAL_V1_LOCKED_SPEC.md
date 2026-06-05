# MAINLINE_FINAL_V1_LOCKED_SPEC

## 封版结论

`Mainline-Final-v1` 的论文主线版本已经冻结为：`p25.1 + explicit recovery phase` 加上 evidence binding / JSON robustness / final-view recommendation / criterion-aware report / offline lifecycle audits。它不是一个继续叠加 controller 的实验分支。

## Runtime 主线包含

- `p25.1 + explicit recovery phase`：保留显式 recovery phase 作为结构化状态修复框架。
- Evidence Binding Robustness：强支持必须绑定到真实 claim，不允许 fallback/unbound support 进入 accept 信号。
- Evidence JSON Robustness：降低 evidence payload parse/fallback 污染。
- Evidence context / empirical structuring：支持 method / empirical / result-oriented support formation。
- Final Recommendation View Runtime v1：输出 `accept_like`、`borderline_positive`、`borderline_insufficient`、`not_assessable_uncertain`、`reject_like`。
- Conservative binary projection：只有严格 `accept_like` 映射为 binary `accept`；二元 accept/reject 只作为 health check。

## Final-view / offline 层包含

- Derived hygiene view：只在 final decision/report 前解释 stale gap、context/meta unresolved、fallback/meta flaw，不修改 live trajectory。
- Criterion-aware final report：覆盖 novelty、significance、technical soundness、empirical adequacy、clarity/reproducibility。
- Support quality audit：区分 real/non-abstract/empirical/method/table/ablation support。
- Hard-negative case study：解释 high-support reject 与 accept-protect 样本。

## 明确不进入主线

- Sticky 系列。
- Throttle / progression gate 系列。
- Support formation pass 作为独立 controller。
- Live state hygiene mutation。
- 全局 fallback suppression。
- Hard-negative prompt family runtime 化。
- 直接调 binary accept/reject 阈值。

## 论文主指标口径

主指标不是 binary accuracy，而是 evidence alignment、support quality、state hygiene、criterion grounding、final-view recommendation distribution 与 recovery process quality。Binary accept/reject 仅作为健康检查和 collapse 诊断。

## 最新 rerun 口径

当前根目录保留的最新结果为 `LATEST_MAINLINE_FINAL_V1_CLOSURE_9B_FULLTEST39_20260504.*`，对应 `mainline_final_v1_closure_9b_fulltest39_20260504`。这轮用于封版 pipeline 的 9B closure rerun：`predicted_accept=1`、`false_accept=0`、`accept_like_ids=['jVEoydFOl9']`。论文表格需固定 gold label 来源，因为这轮 postprocess 口径为 `8 accept / 31 reject`。
