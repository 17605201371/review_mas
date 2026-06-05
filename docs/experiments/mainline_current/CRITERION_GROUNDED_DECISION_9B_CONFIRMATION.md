# Criterion-Grounded Decision 9B Confirmation Audit

## 结论

这轮离线模拟说明：`criterion-grounded aggregation` 在 4B fulltest39 上还不能恢复 accept，但在 9B confirmation subset 上已经能利用 9B 形成的 real support 恢复 accept-like 信号。

关键点不是把 criterion 立即接入 runtime decision，而是：

1. 9B 已经能产生足够多 real-claim support；
2. 当前 final decision 仍然全 reject，说明旧 decision interface 没有使用这些信号；
3. criterion-grounded aggregation 能恢复 4/5 个 accept，但会误翻 1 个 reject（`kam84eEmub`）；
4. 因此下一步是做 **Final Recommendation Policy v1 的安全校准**，不是直接 9B fulltest，也不是让模型自由决定。

## 4B fulltest39 simulation

| mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | borderline | false_accept | recovered_accept |
|---|---:|---:|---:|---:|---:|---:|---|---|
| strict | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 3 | `[]` | `[]` |
| lenient | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` |

## 9B confirmation subset simulation

| mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | borderline | false_accept | recovered_accept |
|---|---:|---:|---:|---:|---:|---:|---|---|
| strict | 0.7500 | 0.7333 | 0.8000 | 0.6667 | 5 | 1 | `['kam84eEmub']` | `['hj323oR3rw', 'LebzzClHYw', 'jVEoydFOl9', 'X41c4uB4k0']` |
| lenient | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | 1 | `['kam84eEmub']` | `['hj323oR3rw', 'LebzzClHYw', 'QAAsnSRwgu', 'jVEoydFOl9', 'X41c4uB4k0']` |

## 9B case interpretation

- recovered accept: `hj323oR3rw`, `LebzzClHYw`, `jVEoydFOl9`, `X41c4uB4k0`。
- borderline accept: `QAAsnSRwgu`，lenient 映射下可恢复，但 strict 下仍保守。
- false accept: `kam84eEmub`。该样本有 high support 和 positive criterion wording，但 gold 是 reject，说明 support/criterion positive 不能作为充分 accept 条件。
- reject/not_assessable: `ZHr0JajZfH`, `TPAj63ax4Y`。

## 决策

- 不建议直接把 criterion aggregation 接入 runtime decision。
- 不建议现在跑 9B fulltest 作为正式主实验。
- 建议先写清 `FINAL_RECOMMENDATION_POLICY_V1.md`：把 final recommendation 明确定义为 `accept_like / reject_like / borderline / not_assessable`，并加入 false-accept safety constraints。
