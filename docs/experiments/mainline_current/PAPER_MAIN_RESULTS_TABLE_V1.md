# Paper Main Results Table v1

## 论文主线定位

本表用于论文主结果草稿。核心结论不是模型已经解决二分类 accept/reject，而是系统能把 runtime state、support quality、criterion grounding 和 final-view recommendation 分层诊断出来。

## Main Results

| component | metric | value | interpretation |
| --- | --- | ---: | --- |
| Runtime health | runtime reject | 39 | runtime final decision 仍然 collapse，不能作为唯一主指标 |
| Runtime health | avg reward | 0.4674 | 仅作为辅助信号 |
| Support state | decision real strong | 37 | 真实 claim strong support，排除 fallback/general claim |
| Support state | non-abstract strong | 18 | 比 abstract-only 更接近论文证据 |
| Support state | empirical strong | 5 | 结果/实验类证据仍不足 |
| Support state | raw fallback strong excluded | 13 | raw state 残留，已从 final-view recommendation 排除 |
| Criterion Sim4 | predicted accept | 10 | 二分类映射召回有限且 false accept 高 |
| Criterion Sim4 | false accept | 7 | 说明不能直接宽松映射 accept |
| Negative anchor | false accept trusted blockers | 0 | 负向 blocker formation 覆盖不足 |
| Negative anchor | recovered accept trusted blockers | 1 | 仍有误伤风险 |
| Support filter | high precision false accept | 0 | 高精度可行但召回低 |
| Support filter | high precision true accept | 1 | 只恢复少量 accept |
| Recommendation view | accept_like | 1 | 高精度正向推荐 |
| Recommendation view | borderline_positive | 12 | 有正向信号但不应硬 accept |
| Recommendation view | not_assessable | 22 | 证据不足时诚实表达不确定性 |
| Metric consistency | accept_like rows with fallback strong | 0 | 确认 fallback raw 残留未污染 accept_like |

## 写论文时的核心表述

1. `accept/reject` 作为 health check，显示传统 final decision 层存在 collapse。
2. `Final Recommendation View` 作为主输出，更符合审稿辅助系统定位。
3. raw fallback-bound support 保留为污染诊断指标，但不进入 decision-eligible support。
4. 当前系统能产生高精度 `accept_like`，但大量样本仍应标为 borderline 或 not_assessable。
