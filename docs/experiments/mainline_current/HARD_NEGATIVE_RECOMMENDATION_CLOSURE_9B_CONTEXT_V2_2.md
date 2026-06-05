# Hard-Negative Grounding + Final Recommendation Closure 9B Context v2.2

## 总判断

网页 GPT 的判断是准确的：当前项目还差的不是 positive support，而是 hard-negative grounding 与 final recommendation policy 收口。

## 已经稳定的部分

- Evidence Binding: `fallback_strong_support_total = 0`，strong support binding precision = `1.0`。
- JSON robustness: evidence json invalid/missing = `0`。
- Positive support: real strong = `49`，non-abstract strong = `49`，empirical strong = `38`。
- Report hygiene: confirmed weakness meta leak rows = `0`。

## 尚未收口的部分

- runtime decision 仍然 `predicted_accept_count = 0`，所以 binary decision 只能是 health check。
- gold reject 中 hard-negative grounding 不足：`negative_unresolved_not_promoted = 13`，`has_grounded_major_or_critical = 1`。
- `borderline_positive = 15` 不能直接 accept，因为它包含大量 gold reject 的 support-positive case。

## 下一刀

建议只做 `Hard-Negative Grounding v2`，并且先离线：

1. 从 `negative_unresolved_not_promoted` 和 `borderline_positive` case 中抽 8-12 条。
2. 对每条提取 empirical/soundness/novelty negative claim。
3. 要求每个 blocker 必须绑定 evidence_id / claim_id / criterion。
4. 输出 blocker 是否足以把 borderline_positive 降为 reject_like 或 not_assessable。
5. 不改变 runtime，不改变 accept/reject 阈值。

## 暂不做

- 不做蒸馏；规格未冻结到可蒸馏阶段。
- 不恢复 sticky/throttle/progression gate。
- 不改 live state hygiene。
- 不把 novelty/soundness 直接裸接入 decision。
