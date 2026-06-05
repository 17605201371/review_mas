# Borderline Positive Next Step Decision v1

## 结论

`borderline_positive` 不应升级为 `accept_like`。15 条中只有 2 条 gold accept，13 条是 gold reject；如果直接把它们映射为 accept，会制造明显 false accept。

## 分布

| bucket | count |
| --- | --- |
| reject_false_accept_risk_no_hard_negative | 8 |
| reject_false_accept_risk_unresolved_heavy | 3 |
| gold_accept_but_unresolved_heavy | 2 |
| reject_false_accept_risk_with_ungrounded_flaw | 2 |

## 解释

当前 positive evidence 已经能形成 real/non-abstract/empirical support，但 paper-level recommendation 仍缺 hard-negative grounding。多数 reject 样本没有 grounded major/critical flaw，因此被 V2 标成 `borderline_positive`；这不是系统应该 accept，而是说明当前 final-view 还无法安全地区分“局部 claim 有支持”和“整篇论文值得接收”。

## 下一刀

下一步唯一建议：`Hard-Negative Grounding Audit v1`。目标是审计 reject 样本中的真实拒稿依据是否被系统抽出并 grounded 到 evidence/criterion/flaw。不要直接调 accept 阈值，也不要把 criterion positive 裸接入 decision。

## 不做

- 不回 sticky / throttle / progression gate。
- 不继续加 Evidence Context，除非 hard-negative audit 证明 reject 样本缺少可见负证据。
- 不把 `borderline_positive` 当作 accept。
