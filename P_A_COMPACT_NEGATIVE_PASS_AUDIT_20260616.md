# P-A Compact Negative Pass Audit - 2026-06-16

## 结论

`DRMAS_NEGATIVE_PASS_MODE=compact` 当前不能进入主线。它保持了 negative quote hygiene 的安全性，但明显压低 positive support、actionable negative flaw 和 recovery repair。

最稳的当前主线仍应是 `DRMAS_NEG_QUOTE_HYGIENE=1` 的 qhyg 版本。P-A compact 只能作为反例/实验开关保留，默认关闭。

## 实验口径

- 数据集：`hard_negative_20_20260611.parquet`
- 模型：`mimo-v2.5`
- 参数：`max_turns=7`、`manager_batch_size=4`、`max_workers_per_turn=2`、`api_max_workers=4`
- 安全层：`DRMAS_NEG_QUOTE_HYGIENE=1`
- compact 开关：`DRMAS_NEGATIVE_PASS_MODE=compact`

## 关键结果

### QHYG baseline

文件：`mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_003753.jsonl`

| metric | value |
|---|---:|
| papers | 20 |
| avg_reward | 0.5764 |
| grounded negative | 12 |
| noise | 0 |
| real strong support | 100 |
| claims with 2+ independent support | 47 |
| verified actionable negative flaw | 8 |
| potential concern | 8 |
| recovery effective repair | 8 |
| mark contested commit | 8 |
| state contamination | 0 |
| evidence gap open | 1 |

### Compact fix3

文件：`mimo_v25_negqty_recoverycap_guard3_qhyg_compactneg_hardneg20_mt7_b4w2_api4_r5t600_20260616_003632.jsonl`

| metric | value |
|---|---:|
| papers | 20 |
| avg_reward | 0.5062 |
| compact turns | 18 |
| grounded negative | 11 |
| noise | 0 |
| real strong support | 67 |
| claims with 2+ independent support | 32 |
| verified actionable negative flaw | 6 |
| potential concern | 6 |
| recovery effective repair | 4 |
| mark contested commit | 4 |
| state contamination | 0 |
| evidence gap open | 4 |

## 判断

第一版 compact 的问题是过度触发且只派 Critique Agent，导致 grounded negative / recovery 归零。

修复版已经改善了结构问题：

- 每篇最多一次 compact checkpoint；
- compact pass 使用 `Evidence Agent + Critique Agent`；
- turn log 记录 `compact_negative_pass_required` 和 `negative_pass_mode`；
- quote hygiene 仍保持 noise=0；
- state contamination 仍为 0。

但修复后仍有实质退化：

- real strong support 明显下降；
- independent support 下降；
- recovery effective repair 减半；
- evidence gap open 增加；
- reward 明显下降。

这说明负向检测即使合并成同轮执行，仍会改变 worker 注意力和输出分布，不能简单理解为“省掉一轮但不影响其它环节”。

## 主线建议

1. 不采纳 `DRMAS_NEGATIVE_PASS_MODE=compact` 进入主线。
2. 保留 qhyg 作为当前安全主线。
3. 后续如果继续做 P-A，不应再压缩 worker routing，而应做更轻的离线/报告层整合。
4. P-B 更值得做：只重排已有 `verify_evidence` 的 target，不新增 live prompt，不改变 worker 类型，不抢 support formation。

