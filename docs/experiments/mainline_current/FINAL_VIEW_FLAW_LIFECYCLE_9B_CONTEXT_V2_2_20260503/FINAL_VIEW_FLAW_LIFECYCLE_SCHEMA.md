# Final-View Flaw Lifecycle Schema v1

## 目标

本 schema 只用于 final-view / offline 派生视图，不改 live `ReviewState`，不改变模型推理轨迹，也不直接调 final decision 阈值。

## Flaw 分类

- `grounded_confirmed_flaw`: 已确认、major/critical 且绑定真实 evidence 的论文缺陷，可作为强 reject blocker。
- `grounded_candidate`: 绑定真实 evidence，但仍是 candidate/open 的疑点。可以进入 Potential Concerns，不应等同 confirmed weakness。
- `weakly_grounded_candidate`: 有 paper/criterion 语言或 evidence id，但没有真实 evidence binding。需要人工复核。
- `ungrounded_candidate`: 没有 evidence/claim grounding 的候选疑点，不应作为强 reject blocker。
- `excerpt_limitation`: 截断、上下文不足、只看到 abstract 等导致的限制，应进入 Review Limitations / Not Assessable。
- `system_meta_limitation`: 系统无法验证、当前 evidence slice 不足等系统侧限制，不应写成论文缺陷。
- `fallback_or_malformed_artifact`: fallback、malformed JSON、raw output 等 artifact，不应进入 Key Weakness。

## Decision view 原则

- 只有 `grounded_confirmed_flaw` 且 severity 为 major/critical 时，才作为强 reject blocker。
- meta / excerpt / fallback 类问题不消失，但转入 `Review Limitations`，不作为论文 weakness。
- accept-like 仍需要真实、非 abstract 的 positive support；本视图不把 abstract-only support 直接升级为 accept。
