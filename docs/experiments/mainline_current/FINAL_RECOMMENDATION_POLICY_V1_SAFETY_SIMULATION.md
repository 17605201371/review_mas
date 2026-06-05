# Final Recommendation Policy v1 Safety Simulation

## 结论

这轮离线 safety simulation 找到了一个可解释、低侵入的第一刀：**negative evidence gate**。

在 9B confirmation subset 上，原始 `sim4_combined` 能恢复 4 个 accept，但误翻 `kam84eEmub`。该 false accept 与 recovered accept 的关键差异是：`kam84eEmub` 有 `negative_evidence_total=1`，而 4 个 recovered accept 的 `negative_evidence_total=0`。

因此，`Final Recommendation Policy v1` 的第一条安全约束应是：

> 当样本存在负向 evidence 时，不允许直接输出 `accept_like`，应降为 `borderline`，等待人工复核或更强 criterion grounding。

这不是 final decision 阈值调参，而是 final-view recommendation 的安全约束。

## 9B confirmation subset

| variant | mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept | borderline |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| `base_sim4_combined` | `strict` | 0.7500 | 0.7333 | 0.8000 | 0.6667 | 5 | `['kam84eEmub']` | `['LebzzClHYw', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu']` |
| `base_sim4_combined` | `lenient` | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | `['kam84eEmub']` | `['LebzzClHYw', 'QAAsnSRwgu', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu']` |
| `safety_a_negative_evidence_gate` | `strict` | 0.8750 | 0.8730 | 0.8000 | 1.0000 | 4 | `[]` | `['LebzzClHYw', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` |
| `safety_a_negative_evidence_gate` | `lenient` | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | `['kam84eEmub']` | `['LebzzClHYw', 'QAAsnSRwgu', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` |
| `safety_b_negative_plus_nonabstract2` | `strict` | 0.6250 | 0.6190 | 0.4000 | 1.0000 | 2 | `[]` | `['X41c4uB4k0', 'jVEoydFOl9']` | `['LebzzClHYw', 'QAAsnSRwgu', 'hj323oR3rw', 'kam84eEmub']` |
| `safety_b_negative_plus_nonabstract2` | `lenient` | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | `['kam84eEmub']` | `['LebzzClHYw', 'QAAsnSRwgu', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['LebzzClHYw', 'QAAsnSRwgu', 'hj323oR3rw', 'kam84eEmub']` |
| `safety_c_minimal_precision_gate` | `strict` | 0.8750 | 0.8730 | 0.8000 | 1.0000 | 4 | `[]` | `['LebzzClHYw', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` |
| `safety_c_minimal_precision_gate` | `lenient` | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | `['kam84eEmub']` | `['LebzzClHYw', 'QAAsnSRwgu', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` |

## 4B fulltest39

| variant | mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept | borderline |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| `base_sim4_combined` | `strict` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | `[]` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `base_sim4_combined` | `lenient` | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_a_negative_evidence_gate` | `strict` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | `[]` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_a_negative_evidence_gate` | `lenient` | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_b_negative_plus_nonabstract2` | `strict` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | `[]` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_b_negative_plus_nonabstract2` | `lenient` | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_c_minimal_precision_gate` | `strict` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | `[]` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |
| `safety_c_minimal_precision_gate` | `lenient` | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` |

## 推荐版本

推荐采用 `safety_a_negative_evidence_gate` 作为下一版离线 policy：

- 在 9B confirmation strict 映射下：恢复 accept，同时 false accept 归零。
- 比 `nonabstract>=2` 更不保守，避免丢掉 `hj323oR3rw` / `LebzzClHYw` 这类只有 1 条 non-abstract support 但 criterion grounding 较强的 accept。
- 比直接 criterion aggregation 更安全，明确处理了 `kam84eEmub` 风险。

## 不建议采用的版本

- `safety_b_negative_plus_nonabstract2`：过于保守，会丢掉部分 recovered accept。
- `safety_c_minimal_precision_gate`：和 negative gate 接近，但当前额外条件没有提供更多收益。

## 下一步

下一步可以进入 `Final Recommendation Policy v1 Dry Run`：

1. 把 negative evidence gate 写入 policy 文档；
2. 在 9B confirmation 和 4B fulltest39 上保持离线评估；
3. 不改 runtime，不跑新模型；
4. 如果 policy 在更大 9B dry run 上仍能恢复 accept 且 false accept 受控，再考虑 9B fulltest。
