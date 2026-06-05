# Negative Blocker Next Cut Decision

## 决策

**下一步不应调 accept/reject 阈值，也不应把当前 criterion aggregation runtime 化。**

9B 已经能形成较多 real-claim support，但 false accept 表明系统缺少可靠的负向证据链：它不能稳定区分“局部 claim 有支持但论文仍有 paper-grounded major weakness”和“系统只是因为上下文不足而无法判断”。

## 下一步唯一建议

进入 **Final-View Negative Blocker View v1**，仍然先做离线或 final-view，不改 live state。

最小目标：

1. 为 flaw 派生 `flaw_source_type = paper_grounded | fallback | system_meta | excerpt_limitation | ungrounded_candidate`。
2. 为 flaw 派生 `flaw_grounding_status = negative_evidence_grounded | positive_only_grounded | dangling_reference | ungrounded`。
3. 为 unresolved 派生 `unresolved_role = paper_weakness_candidate | not_assessable | generic_question | meta_limitation`。
4. final-view aggregation 只允许 `paper_grounded + negative_evidence_grounded + core criterion linked` 的对象作为强 reject blocker。

## 为什么不是继续 support filter

false accept 样本并非只有 shallow support；很多样本同时有 non-abstract / independent support。继续提高 support 阈值会同时挡掉 recovered accept。

## 为什么不是直接用 unresolved/meta count

unresolved/meta burden 在 recovered accept 中也很常见。它应该进入 report limitation 或 not-assessable，而不是直接作为 paper weakness。
