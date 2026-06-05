# Mainline-Final-v1 9B Fulltest39 Decision

## 决策

**暂不进入正式 9B 主试验。**

这轮已经完成 9B fulltest39 dry run，但它暴露出一个比 always-reject 更具体的问题：9B 可以形成 real-claim support，但当前 final-view aggregation 没有足够可靠的 negative blocker / flaw lifecycle 来区分 true accept 与 false accept。

## 为什么不是继续调 support 阈值

false accept 样本并不是只有 abstract-only support。多个 false accept 同时有 non-abstract support、independent support 和 positive grounded criterion。单纯要求更多 support 会同时伤害 recovered accept，并不能稳定区分 reject 样本。

## 为什么不是直接 runtime 化 criterion decision

- Sim 4 strict: false accept = 7, recovered accept = 3
- Sim 4 lenient: false accept = 11, recovered accept = 5

这个水平不适合进入 runtime decision，也不适合作为正式主实验结论。

## 下一步唯一建议

进入 **Final-View Flaw Lifecycle / Meta-Leakage Simulation v1**，只做离线模拟，不改 runtime。

目标是判断：

1. false accept 是否因为 grounded flaw / candidate flaw / meta leakage 没有被正确建模；
2. recovered accept 是否可以在保留 support signal 的同时，去除 stale/meta negative burden；
3. 哪些 negative blockers 应被视为 confirmed paper weakness，哪些只是 system limitation 或 ungrounded candidate。

## 暂停事项

- 不做新的 sticky/throttle/progression gate。
- 不调 final decision 阈值。
- 不把 criterion aggregation 接入 runtime。
- 不把 hygiene 放回 live state。
- 不立即开正式 9B 主实验。
