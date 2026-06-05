# Negative Evidence Anchor Extraction v1

## 定位

本轮只做离线锚点抽取，不改 runtime、不改 final decision。目标是给 negative evidence confirmation pass 提供 result/table/figure/experiment/baseline 等非 abstract 锚点，减少把 context-limited 当 paper flaw 的风险。

## Aggregate

| metric | value |
| --- | ---: |
| rows | 10 |
| rows_with_anchor | 10 |
| avg_anchor_count | 5.5 |
| rows_with_quant_anchor | 10 |

## Anchor Type Counts

| anchor_type | count |
| --- | ---: |
| figure | 10 |
| table | 9 |
| baseline | 9 |
| dataset_metric | 9 |
| results | 9 |
| ablation | 7 |
| limitation | 2 |
