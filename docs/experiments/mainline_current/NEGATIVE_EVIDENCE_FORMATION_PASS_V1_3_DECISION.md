# Negative Evidence Formation Pass v1.3 Decision

## 结论

`Negative Evidence Formation` 方向值得继续，但当前不能接入 final decision。v1.2 能在 false accept 中生成负向 blocker，v1.3 证明其中相当一部分其实是 context-limited blocker，必须降级为 not-assessable。

## 关键数字

- v1.2: false accept trusted blocker `5/7`，recovered accept `1/3`，parse error `0`。
- v1.3 strict precision: false accept strict trusted blocker `2/7`，recovered accept `0/3`。
- v1.3 demoted context-limited blocker: false accept `4/7`，recovered accept `1/3`。

## 判断

当前 pass 已经能形成负向线索，但经常把“abstract / 当前上下文里没看到结果”当成 paper flaw。这个错误不能通过 final decision 阈值修复，也不能把 weak candidate 当 blocker。

## 下一刀

下一步建议做 `Negative Evidence Context Selection v1`：专门给 negative pass 提供 result / table / figure / ablation / limitation 片段，而不是继续扩大 general evidence context。目标是让 blocker 基于真实非 abstract 证据，而不是基于上下文缺失。

## 暂时不做

- 不把 v1.2 blocker 接入 final decision。
- 不用 reviewer comments 做 runtime 输入。
- 不重启 sticky / throttle / progression gate。
- 不调 accept/reject 阈值。
