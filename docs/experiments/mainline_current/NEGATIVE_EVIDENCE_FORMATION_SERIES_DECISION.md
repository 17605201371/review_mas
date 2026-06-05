# Negative Evidence Formation Series Decision

## 总结论

`Negative Evidence Formation / Flaw Confirmation` 方向有研究价值，但当前实现还不能进入 final decision 或正式主线。它能够在 false accept 上产生一部分负向线索，但这些线索很容易和 `not-assessable / context-limited` 混在一起；只要直接当 blocker，就会有误伤 recovered accept 的风险。

## 结果对比

| version | change | false_accept trusted | recovered_accept trusted | parse_error | conclusion |
| --- | --- | ---: | ---: | ---: | --- |
| v1 | 初版多数组 schema | 3/7 | 0/3 | 7/10 high | 有信号，但 JSON 截断严重 |
| v1.1 | 压缩 schema | 1/7 | 0/3 | 5/10 | parse 仍不稳，formation 变弱 |
| v1.2 | `/no_think` + compact JSON | 5/7 | 1/3 | 0/10 | 最强 formation，但 blocker 过宽 |
| v1.3 | strict precision audit | 2/7 | 0/3 | 0/10 | 可区分，但覆盖不足 |
| v1.4 | negative-specific context | 2/7 | 1/3 | 0/10 | context 改动未带来净收益 |

## 关键发现

1. `v1.2` 说明模型能形成负向 evidence/flaw 结构，JSON 稳定性可以通过 `/no_think + compact schema` 修复。
2. `v1.3` 说明很多所谓 blocker 实际是“上下文中没看到结果/表格”，不是 paper-grounded flaw，必须降级为 not-assessable。
3. `v1.4` 说明简单增加 negative context 不能稳定提高可信 blocker，且仍可能误伤 recovered accept。
4. 当前最大缺口不是 final decision 阈值，而是缺少高精度的 paper-grounded negative evidence confirmation。

## 当前不应做

- 不把 v1.2 的 blocker 接入 final decision。
- 不用 weak negative candidate 或 unresolved/meta count 触发 reject。
- 不继续盲目扩 context。
- 不重启 sticky / throttle / progression gate。

## 下一步建议

短期内不要继续 runtime 控制器。下一步应做 **Negative Evidence Precision Case Review**：人工/离线审查 v1.2/v1.3 中的 5 个 false accept blocker 与 1 个 recovered accept blocker，明确哪些是：

- true paper-grounded empirical/soundness flaw；
- context-limited not-assessable；
- abstract-only missing-support 误判；
- valid but insufficiently anchored blocker。

只有明确 precision rule 后，才值得做 `Negative Evidence Formation Pass v2`。
