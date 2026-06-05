# Final-View Unresolved / Candidate-Flaw Classifier v1 Schema

本审计只做离线 final-view 分类，不改 runtime、不改 live `ReviewState`。

## Unresolved 分类

- `system_or_fallback`：fallback / JSON / parser / agent / system 相关，不是论文缺陷。
- `review_context_limitation`：文本截断、excerpt 不足、完整论文缺失，应进入 limitation / not_assessable。
- `resolved_by_support`：相关 claim 已有 real support，但 unresolved 未关闭。
- `paper_empirical_open`：实验、指标、表格、消融等仍未验证的问题。
- `paper_method_open`：方法、机制、算法、训练过程仍未验证的问题。
- `paper_grounded_open`：绑定明确 claim 的 open paper risk。
- `open_review_question`：普通待查问题，不应直接当 weakness。
- `weak_open`：无法可靠归类的 open item。

## Candidate flaw 分类

- `system_or_fallback_flaw`：fallback / malformed JSON / system-meta flaw。
- `review_context_limitation_flaw`：上下文不足导致的 limitation，不能直接作为 paper flaw。
- `confirmed_or_trusted_hard_flaw`：grounded/confirmed high-confidence major/critical flaw。
- `candidate_hard_flaw`：高置信 candidate major/critical flaw，应作为 reject_like 或 not_assessable blocker，但不能等同 confirmed flaw。
