# Fulltest39 Gold Label Lock

## 结论

正式主试验前，fulltest39 的 gold label source 固定为：

- `docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json`

该清单来自最新封版结果的 postprocess gold 文件：

- `LATEST_MAINLINE_FINAL_V1_CLOSURE_9B_FULLTEST39_20260504_gold.jsonl`

锁定计数：

| label | count |
| --- | ---: |
| accept | 8 |
| reject | 31 |
| total | 39 |

Accept ids：

`hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, gzqrANCF4g, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9`

## 使用规则

- 主试验分析脚本必须显式传入 `--gold-labels docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json`。
- 如果输入结果中存在锁定清单没有覆盖的 `paper_id`，脚本应直接报错。
- 不再混用旧表中的 `9 accept / 30 reject` 口径，也不再从 `accept_reject_correct` 反推 gold。
- 如果后续更换 fulltest39 subset，必须生成新的 lock 文件并在报告中显式说明。

## 为什么要锁定

之前存在 `8 accept / 31 reject` 与旧 `9 accept / 30 reject` 的口径混用风险。这个 lock 文件把评估标签从运行结果中剥离出来，保证后续 4B / 9B / confirmation / paper table 使用同一套 gold label。
