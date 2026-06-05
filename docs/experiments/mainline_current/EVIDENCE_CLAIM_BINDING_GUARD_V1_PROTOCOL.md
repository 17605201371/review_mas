# Evidence Claim Binding Guard v1 Protocol

## 目标

本轮修复 Evidence ID Turn-Scoping v1 暴露出的下一层状态问题：Evidence Agent 有时把 evidence 绑定到当前 ReviewState 中不存在的 `claim-1` / `claim-2`，而 final state 实际只有 `claim-fallback-*`。这类 evidence 虽然不应作为真实 claim support，但原先仍以无效 claim_id 留在 final evidence_map 中，污染状态审计和后续报告。

## 改动范围

- 不改 prompt。
- 不改 final decision。
- 不改 recovery / sticky / throttle / progression gate。
- 只在 state merge 的 evidence binding validation 中处理无效 claim_id。

## 规则

1. 如果 evidence.claim_id 不存在于当前真实 claims 中，则设置 `binding_status = invalid_claim_id`。
2. 将无效 claim_id 移到 `original_claim_id`，并清空 `claim_id`。
3. 无效绑定 evidence 不计入 real-claim support。
4. 保留 evidence 文本用于诊断，但不让它伪装成已绑定真实 claim。

## 论文意义

该修复保证 ReviewState 中的 evidence binding 是可审计的：不能让 evidence 指向不存在的 claim。它属于状态卫生修复，不是 positive support formation 增强。
