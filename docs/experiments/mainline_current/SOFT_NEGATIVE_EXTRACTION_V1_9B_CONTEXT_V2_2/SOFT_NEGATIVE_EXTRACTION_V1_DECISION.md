# Soft Negative Extraction v1 Decision

## 结论

本轮用 4B 对 Soft Evidence Recommendation v1 的风险样本做小样本 hard-negative extraction，不改 runtime、不改 final decision。

## 关键数字

- soft_false_accept_risk trusted_blocker_rows: `3 / 7`
- soft_recovered_accept trusted_blocker_rows: `0 / 2`
- soft_false_accept_risk weak_negative_rows: `5 / 7`
- parse_error_rows: `0`

## 判断

如果 false-accept-risk 样本中的 trusted blocker 明显多于 recovered accept，说明 hard-negative extraction 有助于区分 borderline。若两组都很低，说明当前 4B 小 pass 还不能可靠补上 hard-negative，只能作为 not_assessable / human-review 的辅助证据。

## 下一步

不要把本 pass 直接接入 final decision。若要继续，应优先改进 hard-negative prompt / context，或改用 9B 对同一小样本做 confirmation，对比 4B 是否能力不足。
