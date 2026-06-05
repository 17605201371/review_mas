# Hard-Negative Extraction v1 Decision

## 结论

已生成 hard-negative extractor prompt pack。当前验证仍是离线层，不接 runtime。

## Context 可见性

- old 800-char critique excerpt negative terms: `{'empirical': 1, 'soundness': 7, 'novelty': 5, 'negative': 2}`
- new hard-negative context negative terms: `{'empirical': 60, 'soundness': 13, 'novelty': 13, 'negative': 39}`
- new context sources: `{'negative': 15, 'results': 15, 'empirical': 9, 'limitations': 7}`

## 判断

如果 new context 明显暴露更多 empirical/soundness/novelty negative anchors，下一步才值得考虑把 Critique Agent 的 `Critique-Relevant Paper Excerpt` 从 800-char prefix 改成 hard-negative section-aware context。若仍没有足够 negative anchors，则应停止 runtime 改动，把这些样本标为 not_assessable / borderline，而不是强行找 flaws。
