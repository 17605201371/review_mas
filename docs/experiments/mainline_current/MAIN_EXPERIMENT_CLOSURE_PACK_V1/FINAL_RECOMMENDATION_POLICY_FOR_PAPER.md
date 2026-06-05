# FINAL_RECOMMENDATION_POLICY_FOR_PAPER

## 决策口径

论文中不把 runtime binary accept/reject 作为主推荐输出。Binary decision 只用于健康检查，判断系统是否出现 always-reject 或 false-accept collapse。

正式推荐采用 final-view recommendation：

- `accept_like`：正向 support 充足、支持质量较高、没有 grounded hard-negative blocker。
- `borderline_positive`：正向 support 明显，但仍有未验证 gap / blocker；应交给 human review，不自动 accept。
- `borderline_insufficient`：部分 support 存在，但不足以形成 accept-like，且缺少稳定 hard-negative。
- `not_assessable_uncertain`：上下文、target 或 evidence 不足，不能可靠判断。
- `reject_like`：存在 grounded major/critical flaw 或明确 paper-grounded blocker。

## 聚合原则

- Strong support 数量不能直接映射 accept。
- Positive criterion 不能裸接 decision。
- Raw unresolved / gap / candidate flaw 不能直接映射 reject。
- Fallback/meta/context limitation 不能写成 paper weakness。
- `borderline_positive` 与 `borderline_insufficient` 应作为审稿辅助中的 human-review routing。

## 论文表述

可以写为：We do not treat final recommendation as a free-form binary model judgment. We derive an evidence-grounded recommendation view over the final ReviewState and use binary accept/reject only as a diagnostic health check.
