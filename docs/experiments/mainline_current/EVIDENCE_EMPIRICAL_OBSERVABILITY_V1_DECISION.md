# Evidence Empirical Observability v1 Decision

## 保留判断

保留。该补丁是纯观测层，不改变 runtime 行为，能直接回答 empirical support 断点发生在 context、raw output、payload structuring 还是 strong/support 标注阶段。

## 下一步

在下一次 4B/9B 小样本或 fulltest dry-run 后，统计：

- `no_raw_empirical_signal`
- `raw_empirical_no_payload_evidence`
- `raw_empirical_payload_no_empirical_evidence`
- `empirical_payload_without_strong_support`
- `strong_empirical_payload_formed`

如果主要是 `no_raw_empirical_signal`，下一刀才考虑 Evidence Context Selection v2；如果主要是 payload/strong structuring loss，下一刀应改 Evidence JSON/labeling robustness，而不是加长 context。
