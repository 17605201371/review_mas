# Critique Context Selection v1.1 Protocol

本轮验证 Critique Agent 的 800 字前缀上下文是否导致 hard-negative grounding 不足。

- v1: 直接加入 hard-negative section-aware context，但 generic negative anchor 过宽。
- v1.1: 只优先使用 limitations/results/method/related-work 等真实审稿段落，generic negative anchor 延后且限量。
- 本轮不改 final decision、不改 recovery/controller、不改 live state hygiene。
