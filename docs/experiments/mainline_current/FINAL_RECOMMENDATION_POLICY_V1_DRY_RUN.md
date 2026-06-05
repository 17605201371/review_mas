# Final Recommendation Policy v1 Dry Run

## 结论

`Final Recommendation Policy v1` 作为离线 final-view recommendation policy 值得保留，但仍不应接入 runtime decision。

核心规则是：在 criterion/support/hygiene 聚合给出 `accept_like` 后，如果存在 `negative_evidence_total > 0`，则降为 `borderline`。这条 safety gate 在 9B confirmation 上压住了 `kam84eEmub` false accept，同时保留 4 个 recovered accept。

## Policy Rules

1. 基础标签来自 `sim4_combined_criterion_support_hygiene`。
2. 如果 `label == accept_like` 且 `negative_evidence_total > 0`，则改为 `borderline`。
3. strict 映射：`accept_like -> accept`，其他均按 reject 计入 health check。
4. lenient 映射只做上界分析：`borderline -> accept`。

## Results

| dataset | mapping | rows | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | recovered_accept | borderline | not_assessable |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| `4b_fulltest39` | `strict` | 39 | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | `[]` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `['gzqrANCF4g', 'jVEoydFOl9', '7Dub7UXTXN', '9zEBK3E9bX', 'N0isTh3rml', 'YXn76HMetm', 'a6SntIisgg', 'kam84eEmub']` |
| `4b_fulltest39` | `lenient` | 39 | 0.6923 | 0.4091 | 0.0000 | 0.9000 | 3 | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `[]` | `['HPuLU6q7xq', 'TPAj63ax4Y', 'aRxLDcxFcL']` | `['gzqrANCF4g', 'jVEoydFOl9', '7Dub7UXTXN', '9zEBK3E9bX', 'N0isTh3rml', 'YXn76HMetm', 'a6SntIisgg', 'kam84eEmub']` |
| `9b_confirmation` | `strict` | 8 | 0.8750 | 0.8730 | 0.8000 | 1.0000 | 4 | `[]` | `['LebzzClHYw', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` | `['TPAj63ax4Y', 'ZHr0JajZfH']` |
| `9b_confirmation` | `lenient` | 8 | 0.8750 | 0.8545 | 1.0000 | 0.6667 | 6 | `['kam84eEmub']` | `['LebzzClHYw', 'QAAsnSRwgu', 'X41c4uB4k0', 'hj323oR3rw', 'jVEoydFOl9']` | `['QAAsnSRwgu', 'kam84eEmub']` | `['TPAj63ax4Y', 'ZHr0JajZfH']` |

## 判断

- 4B fulltest39 仍无法恢复 accept，说明 4B 的 positive support / criterion grounding 不足。
- 9B confirmation 在 strict 映射下恢复 4/5 个 accept，false accept 为 0，说明 9B + final-view policy 方向成立。
- 由于确认集只有 8 条，不能直接当论文主试验；但已经足够支持下一步做 9B fulltest dry run。

## Next Step

下一步建议进入 `9B Fulltest39 Dry Run`，但仍然保持两个边界：

1. runtime 只使用已保留主线组件，不新增 controller；
2. final recommendation policy 仍作为离线 final-view 层，不改变 live ReviewState。
