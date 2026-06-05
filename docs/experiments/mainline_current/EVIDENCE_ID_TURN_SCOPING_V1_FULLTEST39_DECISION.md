# Evidence ID Turn-Scoping v1 Fulltest39 Decision

## 结论

**保留 `Evidence ID Turn-Scoping v1`。**

## 理由

1. 它修复的是明确的证据覆盖 bug：多轮 Evidence Agent 输出复用相同 evidence_id，旧证据被新证据覆盖。
2. fulltest39 上 evidence retention 明显改善：final evidence total `75 -> 142`，payload duplicate rows `33 -> 2`。
3. final 2+ real strong support rows `1 -> 4`，说明保留更多证据后，positive support 的可见性提高。
4. `invalid_bound 4 -> 23` 是下一层 claim binding 问题暴露，不应通过回退 turn-scoping 解决。

## 风险

- 由于更多证据进入 final state，invalid claim binding、support quality 和 final-view filtering 的问题会更明显。
- 不能把所有保留下来的 strong support 直接作为 accept 依据，后续必须经过 support quality / final-view invalid-binding 过滤。

## 下一步

下一步不应 live 清空 invalid claim_id。应在 final-view / support-quality 层标记并过滤 invalid-bound evidence，避免再次干扰 live trajectory。
