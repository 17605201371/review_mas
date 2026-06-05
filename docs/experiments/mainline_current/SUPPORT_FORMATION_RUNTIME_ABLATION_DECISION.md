# Support Formation Runtime Ablation Decision

## 结论

不保留 `Support Formation Pass` 作为主线 runtime 机制。

这条线的实验价值是明确的：它证明“多补一轮 evidence”可以在某些配置下提高 real-claim strong support，但它不是稳定收益点。更准确地说，当前问题不是 evidence turn 数量不够，而是 evidence turn 的结构化质量、JSON 稳定性、claim binding、non-abstract/empirical support 形成仍不够稳定。

## 对比结果

| variant | real strong | nonabs strong | empirical strong | rows 2+ real strong | patch emitted | patch committed | rows with commit | avg turns | support triggers |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| support_quality_v1 | 0 | 0 | 0 | 0 | 32 | 6 | 5 | 7.31 | 0 |
| support_pass_v1_mt8 | 9 | 9 | 5 | 1 | 7 | 0 | 0 | 4.56 | 16 |
| budget_fix_v1 | 7 | 7 | 5 | 0 | 16 | 0 | 0 | 7.69 | 28 |
| pre_recovery/one_shot | 7 | 0 | 0 | 3 | 13 | 5 | 3 | 8.00 | 0 |

## 失败模式

### 1. 原始 support pass

`support_pass_v1_mt8` 能提高 real/non-abstract/empirical support，但它吃掉一轮后仍被 S4 第 4 轮 auto-finalize 截断，导致 recovery / patch / commit 空间被压缩：

- `patch_committed: 6 -> 0`
- `rows_with_any_commit: 5 -> 0`
- `avg_turns: 7.31 -> 4.56`

### 2. budget fix

`budget_fix_v1` 延后 auto-finalize 后，turn budget 恢复，但 support pass 变成反复抢占 recovery 的机制：

- `support_trigger_turns: 28`
- `patch_emitted: 16`
- `patch_committed: 0`

这说明问题不只是 turn budget，而是 support pass 不能进入 recovery 后继续介入。

### 3. one-shot / pre-recovery 收紧

将 support pass 收紧后，它在当前 mixed16 路径上基本不触发，因为系统已经有大量 `verify_evidence` turn；但这些 turn 没能形成足够 non-abstract / empirical support：

- `support_trigger_turns: 0`
- `nonabs_strong: 0`
- `empirical_strong: 0`
- `fallback_payloads: 40`

这说明继续加 evidence turn 不是主瓶颈。

## 代码处理

主线默认关闭：

```python
ENABLE_SUPPORT_FORMATION_PASS = False
```

保留 helper 和日志字段用于后续受控 ablation，但不让它影响主线 runtime。

## 下一步

不要继续沿 runtime support-pass controller 方向钻下去。

下一步应回到已经更稳定的主线：

1. 保留 Evidence Binding Robustness v1。
2. 保留 Evidence JSON Robustness v1.1。
3. 保留 final-view hygiene 与 criterion-aware report 作为 offline / final-view 层。
4. 下一刀优先做 Evidence JSON / evidence extraction robustness，而不是再加 runtime 控制器。

## 当前判断

`Support Formation Pass` 是一个诊断性实验，不是主线改进。它证明 positive support formation 是关键问题，但修法不应是“多给一轮 verify_evidence”，而应是让已经存在的 evidence turn 产出更稳定、更深、更能绑定真实 claim 的结构化 evidence。
