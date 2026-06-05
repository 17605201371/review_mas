# Support Formation Pass v1 对比结果

## 配置说明

正式对比使用同一批 16 条 mixed subset，且 baseline / candidate 均按 `max_turns=8` 解读。早期 `max_turns=5` 的 candidate 结果不用于最终判断。

## 汇总指标

| 指标 | Baseline | Support Formation v1 mt8 | 变化 |
|---|---:|---:|---:|
| rows | 16 | 16 | 0 |
| avg_reward | 0.3892 | 0.4427 | +0.0535 |
| predicted_accept | 0 | 0 | 0 |
| real-claim strong support | 0 | 9 | +9 |
| fallback-claim strong support | 0 | 0 | 0 |
| rows with 2+ real strong support | 0 | 1 | +1 |
| support formation triggers | 0 | 16 | +16 |
| rows with trigger | 0 | 15 | +15 |
| verify_evidence turns | 25 | 33 | +8 |
| unresolved questions | 127 | 107 | -20 |
| flaw candidates | 19 | 23 | +4 |
| total turn logs | 117 | 73 | -44 |

## 逐样本要点

- `bcHty5VvkQ` 从 0 个 real strong support 提升到 2 个，是唯一达到 2+ real strong support 的样本。
- `cWEfRkYj46`、`VEJzjAvaIy`、`giU9fYGTND` 等样本 reward 明显上升，但仍未恢复 accept。
- `JdWpIe70FL`、`k243qi7S50`、`xYzOkOGD96` 有小幅回退，说明这项 runtime pass 并非无副作用。
- fallback-claim strong support 仍为 0，说明 Evidence Binding Robustness v1 没被破坏。

## 主要观察

### 正向信号

1. support formation pass 真实 actuation：16 次触发，15/16 行至少触发一次。
2. real-claim strong support 从 0 提升到 9。
3. fallback strong support 没有回升，新增 support 基本仍绑定在真实 claim 上。
4. unresolved 总数从 127 降到 107。
5. 平均 reward 从 0.3892 升到 0.4427。

### 仍未解决的问题

1. predicted accept 仍为 0。
2. 2+ real strong support 只有 1 行，距离恢复 accept-like state 仍不足。
3. flaw candidates 从 19 增到 23，说明多一次 evidence pass 也可能带来更多负面对象。
4. 总 turn logs 从 117 降到 73，说明 support pass 改变了后续轨迹，不是纯粹“多加一轮 evidence”那么简单。

## 结论

Support Formation Pass v1 证明“在进入 flaw/recovery/final 前补一次 evidence”是有效信号：它能增加真实 claim strong support，且没有重新引入 fallback support 污染。但它不足以独立解决 always-reject，也不能作为最终论文主结论。
