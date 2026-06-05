# Oracle Negative Evidence Formation Audit v1

## 定位

本审计使用 `reviewer_comments` 作为离线 oracle-style 参照，只用于诊断，不进入 runtime，不作为模型输入。目标是判断：9B false accept 是否因为人工评审中存在 hard/core weakness，而系统没有形成 trusted negative blocker。

## 结论

false accept 中存在明显的 negative evidence formation gap：如果人工评审指出 core hard weakness，而系统 final-view 中没有 trusted negative blocker，那么当前 false accept 不是 support 阈值问题，而是负向证据没有被形成/确认。

## Aggregate

| group | metric | value |
| --- | --- | --- |
| false_accept | rows | 7 |
| false_accept | oracle_core_hard_weakness_rows | 7 |
| false_accept | system_trusted_blocker_rows | 0 |
| false_accept | formation_gap_rows | 7 |
| false_accept | avg_oracle_hard_weakness_count | 6.286 |
| recovered_accept | rows | 3 |
| recovered_accept | oracle_core_hard_weakness_rows | 3 |
| recovered_accept | system_trusted_blocker_rows | 0 |
| recovered_accept | formation_gap_rows | 3 |
| recovered_accept | avg_oracle_hard_weakness_count | 5.333 |


## 解释

- 如果 false accept 的 `oracle_core_hard_weakness_rows` 高，而 `system_trusted_blocker_rows` 低，说明系统漏掉了人工评审实际使用的 reject 依据。
- 如果 recovered accept 也有大量 oracle hard weakness，则说明 gold / reviewer comments 本身复杂，不能直接用 oracle weakness count 当 reject rule。
- 本审计只用于决定下一步是否值得做 Negative Evidence Formation / Flaw Confirmation，不用于直接决策。
