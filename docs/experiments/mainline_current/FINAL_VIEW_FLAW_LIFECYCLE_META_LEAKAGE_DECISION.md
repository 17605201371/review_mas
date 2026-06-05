# Final-View Flaw Lifecycle / Meta-Leakage Decision

## 决策

**不要把当前 lifecycle / meta-leakage filter 接入 runtime decision。**

这轮证明了当前 final-view policy 的主要缺口：false accept 不是因为 support 数量太低或单纯 meta 泄漏，而是因为系统没有可靠地区分：

- grounded paper weakness；
- ungrounded candidate flaw；
- fallback/meta flaw；
- excerpt/context limitation；
- unresolved question。

## 下一步唯一建议

进入 **Criterion-Linked Negative Evidence / Flaw Grounding Audit v1**，仍然先做离线，不改 runtime。

目标是对每个 false accept 与 recovered accept 检查：

1. 是否存在与 empirical/soundness/novelty 直接相关的负向 evidence；
2. 当前 flaw candidate 是否有 paper-grounded evidence；
3. unresolved question 是否只是 not-assessable，还是已经构成 paper weakness；
4. 哪些 negative blockers 应该进入 final-view aggregation，哪些只能进入 report limitation。

## 为什么不是继续调 accept policy

简单 demotion 规则要么挡不住 false accept，要么同时挡掉 recovered accept。当前需要的是更好的负向 evidence / flaw grounding，而不是更复杂的阈值。

## 暂停事项

- 不 runtime 化 criterion aggregation。
- 不把 unresolved/meta count 直接当 reject rule。
- 不改 live state。
- 不重启 sticky/throttle/progression gate。
