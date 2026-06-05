# Criterion-Linked Negative Evidence / Flaw Grounding Schema v1

## 定位

本审计是离线 final-view 分析，不改 runtime、不改 final decision、不重跑模型。目标是解释 9B fulltest39 中 criterion aggregation 为什么会产生 false accept。

## 核心区分

- `trusted_negative_blocker`: 与 empirical/soundness 等核心维度相关、绑定真实 evidence、且可视为 confirmed paper weakness 的负向 blocker。
- `weak_negative_blocker`: 有一定 paper-grounded 负向信号，但仍可能只是 candidate 或 unresolved。
- `meta / fallback flaw`: 来自 fallback、parse、system limitation、excerpt limitation 的负面对象，不能直接当 paper weakness。
- `not_assessable_burden`: meta unresolved、generic unresolved、missing support gap 的合计，只说明系统不确定性或上下文不足，不能直接等同 reject。

## 关键原则

support 可以支持 accept-like，但必须由可信的 negative blocker 来阻止 false accept。当前审计不把 unresolved/meta 数量直接当 reject rule，而是判断这些对象是否真正 paper-grounded。
