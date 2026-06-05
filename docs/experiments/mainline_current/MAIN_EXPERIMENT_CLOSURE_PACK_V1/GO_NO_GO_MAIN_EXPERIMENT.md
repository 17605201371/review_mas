# GO_NO_GO_MAIN_EXPERIMENT

## 结论

Go for main-experiment closure / paper writing. No-Go for adding new runtime controllers.

## Go 条件满足情况

- 最新 9B fulltest39 closure rerun 已完成，并保留到根目录。
- Evidence binding 与 JSON robustness 已稳定：`fallback_strong_support_total=0`。
- Criterion-aware report 可以稳定生成：五个维度 39/39 覆盖。
- Final-view recommendation 已安全恢复 `1` 个 accept_like，未引入 false accept。
- Hard-negative limitation 已有 casebook 支撑。

## No-Go 条件

- 不应把 binary accept/reject accuracy 当主结果。
- 不应把 hard-negative extraction runtime 化。
- 不应继续 sticky / throttle / progression gate。
- 不应为提升 accept recall 直接放宽 binary threshold。

## 下一步

如果继续实验，只做封版 pipeline 的复现性确认或更大样本验证；否则进入论文写作：方法、主结果表、case study、limitation / discussion。
