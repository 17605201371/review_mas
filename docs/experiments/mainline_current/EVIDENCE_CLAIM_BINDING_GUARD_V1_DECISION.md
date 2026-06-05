# Evidence Claim Binding Guard v1 Decision

## 结论

**不保留 runtime `Evidence Claim Binding Guard v1`。**

该实验应作为负结果保留：它证明 invalid claim binding 是真实问题，但也证明在 live state merge 阶段清空 invalid `claim_id` 会伤害 accept-side positive support formation。

## 为什么 mixed16 的正向结论被推翻

mixed16 中，guard 让 `invalid_bound 8 -> 0`，avg_reward 和 gaps 看似改善，所以曾经判断为可进入 fulltest 确认。但 fulltest39 暴露了更关键的问题：

- `accept_final_real_strong: 3 -> 1`
- `accept_rows_final_2plus_real: 1 -> 0`
- `accept_payload_real_strong: 9 -> 1`
- `invalid_bound: 23 -> 0` 的代价是 `invalid_unbound: 0 -> 19`

这说明 guard 不是把无效绑定修成有效绑定，而是把一批 evidence 从 claim-linked path 中移除，导致 accept 样本的 positive support 被压缩。

## 当前正确边界

保留：

- `Evidence ID Turn-Scoping v1`，因为它修复 evidence_id 覆盖。
- invalid binding 的观测指标和 case table。

不保留：

- live state merge 阶段清空 invalid `claim_id`。
- 用 runtime guard 直接改变 Evidence Agent 形成的 state trajectory。

## 下一步

下一步应实现或验证 **Final-View Invalid Binding Filter / Support Quality Decision View**：

1. 在 final-view 中标记 `invalid_bound / invalid_unbound / fallback_bound` evidence。
2. 这些 evidence 不进入 accept 所需的 real-claim strong support 计数。
3. 不修改 live ReviewState，不影响后续 evidence formation / recovery trajectory。
4. 在 criterion-grounded / support-quality decision simulation 中统一评估。
