# Support Formation Pass v1 决策

## 最终判断

**保留 Support Formation Pass v1 作为当前主线的轻量 support-formation guard，但不继续沿这个方向叠加更多 controller。**

理由：

- 它在同口径 `max_turns=8` 下真实提升了 real-claim strong support：0 -> 9。
- fallback strong support 仍为 0，没有破坏 Evidence Binding Robustness v1。
- 平均 reward 上升，unresolved 总数下降。
- 但它没有恢复 accept，2+ real strong support 只有 1 行，说明它只是修补 positive support formation 的一部分。

## 为什么不继续加更强 controller

这轮结果说明，系统不是完全没有机会形成 positive support，而是 evidence formation 仍不够深、不够稳定。继续通过 manager policy 强插更多 evidence turn，可能会带来三个问题：

1. 改变 live trajectory，造成新的不稳定。
2. 增加 flaw / unresolved 负担。
3. 把问题重新拉回 controller 调参，而不是解决 evidence quality 与 final-view interpretation。

因此下一步不应继续做 Support Formation Pass v2 / v3。

## 下一步建议

下一步应转向**离线层面的 support quality 与 criterion grounding 结合分析**，或者在 final-view 侧做更精细的 support-quality view，而不是继续改运行时 controller。

优先方向：

1. 继续使用 Evidence Binding Robustness v1 + Support Formation Pass v1 作为当前 runtime 底座。
2. 用现有 mixed16 / fulltest 结果审计：新增的 real strong support 是否来自 method/result/table/ablation，而不是浅层 abstract claim。
3. 对 final-view hygiene 加入 support quality 维度，但先做离线模拟，不直接改 final decision 阈值。

## 当前结论一句话

Support Formation Pass v1 有价值，但它是“补一次证据形成机会”，不是最终 accept 恢复机制；论文主线仍应聚焦 evidence binding、derived hygiene view、criterion-grounded review，而不是继续堆硬控制器。
