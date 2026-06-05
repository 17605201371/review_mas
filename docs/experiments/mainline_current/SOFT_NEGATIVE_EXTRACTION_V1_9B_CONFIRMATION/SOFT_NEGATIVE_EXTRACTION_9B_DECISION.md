# Soft Negative Extraction 9B Decision

## 结论

本轮用 9B 对同一 9 条 Soft Evidence Recommendation v1 风险样本做 hard-negative extraction confirmation，不改 runtime、不改 final decision。

## 关键数字

- soft_false_accept_risk trusted_blocker_rows: `0 / 7`
- soft_recovered_accept trusted_blocker_rows: `0 / 2`
- soft_false_accept_risk weak_negative_rows: `1 / 7`
- parse_error_rows: `2`

## 判断

如果 9B 相比 4B 能在 false-accept-risk 样本里形成更多 trusted blocker，同时不误伤 recovered accept，说明 hard-negative extraction 是值得进入下一轮主线验证的候选模块。若仍不稳定，则保持为 offline/human-review 辅助层。
