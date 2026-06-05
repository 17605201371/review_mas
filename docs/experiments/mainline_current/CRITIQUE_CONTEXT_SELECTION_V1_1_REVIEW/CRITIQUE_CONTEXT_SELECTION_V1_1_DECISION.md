# Critique Context Selection v1.1 Decision

## 决策

不保留 runtime 改动，恢复到 clean Mainline-Final-v1 代码。

## 原因

1. hard-negative context 可见性确实提升，但 runtime 结果没有净收益。
2. v1/v1.1 均未改善 accept/reject health，runtime 仍为 39/39 reject。
3. v1.1 相比 clean baseline 仍增加 targetless unresolved 与 fallback/meta flaw，说明 Critique 上下文扩展会放大未验证负担。
4. grounded major/critical flaw 只从 2 增至 3，不足以抵消 commit 与 state hygiene 退化。

## 下一步

保持 clean runtime，不继续增加 Critique prompt/controller。下一步应做 `Final-View Flaw Lifecycle / Meta-Leakage Filter`：在 final-view/report 层区分 grounded confirmed flaw、ungrounded candidate、fallback/meta flaw 与 not_assessable，不改 live ReviewState。
