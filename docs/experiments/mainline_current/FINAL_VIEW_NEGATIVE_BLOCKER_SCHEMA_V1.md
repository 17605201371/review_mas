# Final-View Negative Blocker View v1 Schema

## 定位

这是一个离线派生视图，不改 runtime、不改 live ReviewState、不改 final decision。它的作用是把 final-view 中的负向对象分成可决策与不可决策两类。

## 标签

- `strong_reject_blocker`: confirmed / paper-grounded / negative-evidence-grounded / core criterion linked，可以作为 accept-like 的强 blocker。
- `weak_negative_candidate`: 有 paper-grounded 负向候选，但仍不是 confirmed weakness，只能进入 human review 或 report warning。
- `not_assessable_burden`: 上下文不足、generic unresolved、missing-support gap 过多，应进入 not-assessable / limitation，而不是直接 reject。
- `meta_limitation_only`: fallback、system、excerpt limitation 等元信息，只能作为 report limitation。
- `positive_support_without_negative_blocker`: 有正向 support，但没有可信负向 blocker；不能直接 accept，也不能直接 reject。
- `partial_support_no_negative_blocker`: 有部分支持但不足以形成 paper-level recommendation。
- `no_clear_signal`: 正负信号都不足。

## 原则

负向 blocker 必须比 support filter 更严格。不能用 unresolved/meta count 直接触发 reject；也不能用局部 positive support 直接触发 accept。
