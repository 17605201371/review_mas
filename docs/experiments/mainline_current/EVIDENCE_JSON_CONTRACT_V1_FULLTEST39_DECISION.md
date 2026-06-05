# Evidence JSON Contract v1 Fulltest39 决策

## 结论

**保留 Evidence JSON Contract v1。**

它在 4B fulltest39 上没有解决 final decision collapse，但解决的是更靠前、更关键的状态构建问题：Evidence Agent 的 parse failure 不再大量进入 fallback payload，并且 strong support 没有重新污染到 fallback claim。

## 关键指标

- Evidence fallback payloads: `22 -> 2`
- fallback strong support: `0 -> 0`
- real strong support: `10 -> 13`
- non-abstract strong support: `5 -> 10`
- empirical strong support: `8 -> 13`
- unresolved total: `209 -> 234`
- candidate flaws: `58 -> 45`

## 边界

本轮不要继续在 Evidence JSON contract 上钻牛角尖。仍有 `33` 次 parse error，但 fallback payload 已经被控制住，当前更值得处理的是 final-view 层：stale negative burden、flaw lifecycle、criterion-grounded aggregation。

## 下一步

基于 `outputs/results_main/review_infer/evidence_json_contract_v1_fulltest39_4b_merged.jsonl` 做：

1. final-view hygiene simulation；
2. support quality / evidence independence audit；
3. criterion-grounded decision simulation；
4. 统一主线 fulltest39 报告。
