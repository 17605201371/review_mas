# MAINLINE_FINAL_V1_GO_NO_GO

## 结论

当前版本可以进入论文结果整理和主试验预跑，不建议继续研发新 controller。

## Go

- 使用 `Mainline-Final-v1` 作为论文主线 pipeline。
- 报告 evidence binding、JSON robustness、support quality、hard-negative grounding、criterion grounding、final-view recommendation。
- 把 runtime binary accept/reject 作为 health check，而不是主指标。
- 把 `borderline_positive` 解释为 human-review / borderline，不映射为 accept。
- 把 soft negative extraction 作为离线诊断材料，不接入 runtime。

## No-Go

- 不继续 sticky / throttle / progression gate。
- 不再靠硬阈值调 accept/reject。
- 不把 novelty / soundness / empirical adequacy 裸接入 final decision。
- 不把 context limitation、targetless unresolved 或 unverified hard-negative 当作 paper weakness。

## 下一步

1. 用本结果包写论文主结果与 failure analysis。
2. 如需正式主试验，保持同一 pipeline，只跑冻结配置，不再叠加新机制。
3. 若导师要求更饱满的审稿维度，使用 criterion-aware report 与 grounding audit，而不是 criterion-based decision rule。
