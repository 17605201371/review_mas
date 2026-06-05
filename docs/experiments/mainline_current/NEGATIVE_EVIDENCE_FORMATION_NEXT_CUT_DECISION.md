# Negative Evidence Formation Next Cut Decision

## 决策

下一步应做 **Negative Evidence Formation / Flaw Confirmation v1**，但仍建议先在小样本上运行，不直接进入正式主实验。

## 原因

9B 已经能形成 real-claim support，但 false accept 表明系统没有可靠形成 paper-grounded negative blocker。`reviewer_comments` 离线参照可以帮助确认：人工评审实际指出的 empirical/soundness/novelty weakness 是否被系统漏掉。

## 最小实现目标

1. 在 final-view 或小样本 pass 中专门抽取 negative evidence，优先围绕 empirical/soundness/novelty。
2. 把 negative evidence 绑定到真实 claim、criterion 和 flaw candidate。
3. 只把 `paper_grounded + negative_evidence_grounded + core criterion linked` 的 flaw 升为 strong blocker。
4. meta / fallback / excerpt limitation 只能进入 report limitation 或 not-assessable。

## 暂时不做

- 不调 accept/reject 阈值。
- 不 runtime 化 criterion aggregation。
- 不把 reviewer_comments 用作 runtime 输入。
- 不重启 sticky/throttle/progression gate。
