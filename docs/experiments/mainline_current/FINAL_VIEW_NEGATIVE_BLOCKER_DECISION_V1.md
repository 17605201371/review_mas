# Final-View Negative Blocker Decision v1

## 决策

**当前不应把 negative blocker view 接入 final decision。**

这轮视图的价值是诊断：它证明系统缺少足够的 `strong_reject_blocker`，所以 criterion aggregation 会把部分有局部 support 的 reject 样本误判为 accept-like。

## 下一步

下一步应优先做 **Negative Evidence Formation / Flaw Confirmation v1**，但仍建议先离线或小样本，不直接进入正式主试验。

目标不是继续调 decision rule，而是让系统能形成如下对象：

- 与 empirical/soundness 相关的 negative evidence；
- paper-grounded candidate flaw；
- confirmed major flaw；
- not-assessable limitation 与 paper weakness 的明确边界。

## 当前暂停

- 不 runtime 化 final recommendation policy。
- 不把 unresolved/meta count 当 reject rule。
- 不继续提高 support 阈值。
- 不重启 sticky/throttle/gate。
