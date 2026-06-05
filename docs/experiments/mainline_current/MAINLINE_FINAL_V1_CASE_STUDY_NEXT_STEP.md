# Mainline-Final-v1 Case Study Next Step

## 当前判断

当前已经不适合继续做 runtime controller。`Evidence ID Turn-Scoping v1` 应保留；`Claim Binding Guard v1` 不应保留；`Final-View Invalid Binding Filter v1` 应作为离线分析层保留。

## 为什么不继续调 final decision

strict support-quality view 恢复 `1` 个 accept，但产生 `2` 个 false accept。说明现在的关键不是简单放宽或收紧阈值，而是解释哪些 support 真正 paper-level sufficient。

## 当前主要 failure taxonomy

| taxonomy | count |
| --- | --- |
| reject_like_no_valid_support | 21 |
| false_reject_no_valid_real_support | 7 |
| borderline_valid_support | 5 |
| false_accept_support_ignores_grounded_flaw | 2 |
| reject_like_grounded_critical | 2 |
| recovered_accept_valid_support | 1 |
| false_reject_insufficient_independent_support | 1 |

## 下一步

下一步应进入论文结果收口：

1. 固定 `Evidence ID Turn-Scoping v1` 作为 runtime 保留组件。
2. 将 invalid-binding / support-quality / criterion-grounding 作为 final-view 诊断指标写入主实验表。
3. 用 case study 解释 recovered accept、false accept 和 false reject 的机制。
4. 不再新增 sticky/throttle/gate 或 live state hygiene mutation。
5. 若还要跑实验，应只做最终 9B confirmation 或论文主表复现实验，不再大改框架。
