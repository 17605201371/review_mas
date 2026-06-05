# Final-View Hard-Negative / Unresolved Lifecycle Decision v1

## 结论

离线 simulation 支持继续推进 final-view lifecycle 方向，但当前不应 runtime 化，也不应放宽 accept-like。

关键原因：

- raw unresolved 总量为 `190`，派生后 active unresolved 仍为 `57`，说明确实存在大量未关闭/未分层的 negative burden。
- stale / meta / fallback burden 为 `199`，说明 final report/decision 前有必要做 derived cleanup。
- strict lifecycle rule 恢复 accept：`LebzzClHYw`，false accept：`无`。
- high-precision lifecycle rule 恢复 accept：`LebzzClHYw`，false accept：`无`。
- soft lifecycle rule 恢复 accept：`LebzzClHYw`，false accept：`无`。

## 下一步

下一步不直接改 live state。建议实现一个更精细的 **Final-View Unresolved Classifier v1**，只服务 final decision/report derived view：

1. 将 `open_review_question`、`meta_or_system`、`resolved_by_support` 从 paper weakness 中分离。
2. 将多项 `candidate_only_hard_negative` 作为 `reject_like` 或 `not_assessable`，不能忽略。
3. 只让 `paper_grounded_open` 和可信 confirmed/grounded flaw 进入强 reject blocker。
4. 对 `not_assessable` 单独报告，不映射成 reject 或 accept。

## 暂不做

- 不调 runtime accept/reject 阈值。
- 不恢复 sticky/throttle/progression gate。
- 不把 hygiene 放入 `_refresh_state_consistency()`。
