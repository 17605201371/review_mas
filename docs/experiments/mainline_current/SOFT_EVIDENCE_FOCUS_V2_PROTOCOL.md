# Soft Evidence Focus v2 Protocol

## 目标

`Accept-Side Evidence Focus v1` 证明 accept 样本需要更窄、更核心的 evidence target，但 top-2 hard focus 压缩了全局 evidence exploration。`Soft Evidence Focus v2` 只改 Evidence Agent observation 层，把 hard truncation 改成 preferred ordering。

## 改动范围

只改 Evidence Agent 看到的 claim 排序和提示，不改：

- manager action / controller
- recovery / sticky / throttle / progression gate
- final decision
- fallback / binding / lifecycle
- reward

## 规则

当 Evidence Agent action 属于 `verify_evidence` 或 `request_evidence_recheck`，且真实 claim 数量大于 2 时：

1. 根据 importance、empirical/method terms、是否已有 strong support、claim status 对 claim 排序。
2. 选 top-2 作为 `evidence_focus_preferred_claim_ids`。
3. 仍保留最多 4 个真实 claim 作为 `allowed_claim_ids`，不再硬截断为 top-2。
4. Evidence observation 中加入 guidance：优先为 preferred claims 找证据，但如果 secondary claims 有具体 method/result/table support，也允许输出。

## 日志字段

新增/补齐：

- `evidence_focus_mode = soft_preferred_claims_v2`
- `evidence_focus_applied`
- `evidence_focus_reason`
- `evidence_focus_original_claim_ids`
- `evidence_focus_selected_claim_ids`
- `evidence_focus_preferred_claim_ids`
- `evidence_focus_original_claim_count`
- `evidence_focus_selected_claim_count`
- `evidence_focus_preferred_claim_count`

## 判定标准

v2 只有在同时满足以下条件时才建议进入候选主线：

- accept-side real/non-abstract/empirical strong support 不低于 Focus v1。
- 全局 real/non-abstract support 接近或高于 Context v2。
- broad target turns 不高于 Context v2。
- fallback strong support 保持 0。
- evidence JSON fallback 不回升。
- runtime final decision 不作为保留条件，只作为 health check。
