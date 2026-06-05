# Evidence Support Strength Calibration v1 Decision

## 是否保留 runtime 改动

不保留，也不实现 runtime medium->strong promotion。

## 原因

gold accept 的 medium support 主要来自 abstract self-claim；全量升级会把大量 gold reject 一起翻成 accept。non-abstract/empirical 限定虽然更安全，但覆盖太少，不能解决 accept support formation。

## 下一步唯一建议

进入 `Evidence Context Selection v2 / Accept-Side Evidence Formation v2`：不是继续加长上下文，而是在 Evidence Agent 输入和提示中优先要求 method/results/table/ablation 证据，并要求每个 high-importance real claim 至少尝试抽取一条 non-abstract support。仍先用 4B mixed/fulltest 小闭环验证。
