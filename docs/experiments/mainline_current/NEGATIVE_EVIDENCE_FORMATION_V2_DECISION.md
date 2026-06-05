# Negative Evidence Formation v2 Decision

## 结论

v2 规则可以显著降低 blocker 过宽问题，但覆盖仍不足，暂时不能接入 final decision。

## 关键结果

- false accept: v1.2 trusted rows `5/7` -> v2 trusted rows `2/7`。
- recovered accept: v1.2 trusted rows `1/3` -> v2 trusted rows `0/3`。

## 判断

如果 v2 能把 recovered accept blocker 降到 0，同时保留一部分 false accept blocker，说明 precision 方向正确。但如果 false accept 覆盖过低，下一步不能靠 final decision 使用它，而应继续改 negative evidence formation 的 evidence retrieval / anchor extraction。

## 下一步

建议做 `Negative Evidence Anchor Extraction v1`：离线抽取 result/table/figure/experiment 附近原文锚点，再让 pass 只基于这些锚点确认 flaw。不要继续使用 abstract/context-missing 作为负向依据。
