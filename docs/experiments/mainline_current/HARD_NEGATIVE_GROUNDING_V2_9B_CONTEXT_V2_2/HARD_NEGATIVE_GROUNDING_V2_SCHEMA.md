# Hard-Negative Grounding v2 Schema

本层是离线 final-view 修复，不改 runtime。v2 的关键变化是：

- `review_context_limitation`: 截断、excerpt、full text unavailable、fallback/malformed/system 相关内容，不能当 hard-negative。
- `grounded_actionable_hard_negative`: empirical 或 soundness 负面疑点，且绑定 evidence、real claim 或 criterion grounding。
- `ungrounded_negative_unresolved`: 有负面语义但没有 evidence/claim/criterion grounding，只能触发 not_assessable，不能触发 reject_like。
- `candidate_grounded_hard_flaw`: major/critical candidate，已有 grounding，但未 confirmed；可作为 reject_like blocker 的候选，需要人工复核。
