# Positive Support Next Cut Decision

**运行行为是否改变**：否。

## 1. 必答结论

```text
positive support 最早断点是：输入层 / Evidence Context Selection
主要发生在：agent_system.environments.env_package.review.state._render_paper_excerpt -> render_evidence_observation -> agent_system.inference.review_runner.build_worker_observation
accept 样本 strong support 缺失的主因是：Evidence Agent 只看到固定开头短 excerpt，且该 excerpt 经常包含 instruction wrapper + title/abstract 开头，method/result/table 证据不可见，导致 raw 阶段就缺少可用 positive support。
parse failure 是否是主因：不是最早主因，但属于放大器；Evidence Agent parse_error=151/369，fallback_payload=127/369。
fallback-bound support 是否是主因：不是 mixed v2 上的最早断点，因为 strong support 总量本身不足；但它是安全约束，当前 strong fallback-bound=9，不能直接计入 accept。
下一轮唯一建议实现的是：Evidence Context Selection v1
暂时不要做的是：final decision threshold 放松、sticky/throttle/progression gate、recovery controller、全局 fallback suppression、candidate flaw/unresolved runtime 清理、直接把 fallback-bound support 当 accept 证据。
```

## 2. 支撑数据

| metric | value |
|---|---|
| total_samples | 71 |
| accept_samples | 26 |
| accept_samples_without_real_claim_strong_support | 17 |
| accept_samples_context_not_support_possible | 24 |
| final_strong_positive_total | 54 |
| final_strong_positive_real_claim | 45 |
| final_strong_positive_fallback_claim | 9 |
| evidence_agent_calls | 369 |
| evidence_agent_parse_errors | 151 |
| evidence_agent_fallback_payloads | 127 |

## 3. 为什么不是其他方向优先

- **不是 final decision threshold**：`strong<2` 多数时候反映的是 ReviewState 里没有可靠 positive support，而不是 threshold 单点过严。
- **不是 runtime state hygiene 优先**：mixed v2 的 C1-C4 清负面模拟没有 recovered accept，说明正向 support 缺失时清负面也无效。
- **不是 Claim-Evidence Reconciliation 优先**：只有当 real-claim strong support 已形成但 status 未同步时，它才是最早修复点；当前更早断在 context/抽取。
- **不是全局 fallback suppression**：fallback 有污染风险，但也可能保留诊断信号；应先让 Evidence Agent 看到正确上下文。

## 4. 下一轮唯一实验定义

**Evidence Context Selection v1**：只改 Evidence Agent 的可见论文上下文选择，不改 decision、不改 recovery、不改 sticky/gate/throttle。目标是让 Evidence Agent 至少看到 abstract + method/result/evaluation/conclusion 或 table/figure 附近片段，而不是固定 `paper_text[:800]`。
