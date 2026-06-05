# Hard-Negative Grounding Audit v1

## 结论

gold reject 样本 `30` 条，其中 balanced-only false-accept risk `2` 条。风险样本的共同点是 positive support 足以触发 balanced，但 empirical support / empirical criterion 不足，且没有被可靠 hard-negative blocker 拦住。

## Balanced false-accept risk table

| paper_id | calibrated | audit_label | real | nonabs | empirical_support | empirical_criterion_grounded | grounded_negative_flaws | negative_empirical_evidence | unresolved_empirical |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kam84eEmub | borderline_positive | false_accept_risk_positive_not_sufficient | 4 | 1 | 0 | False | [] | [] | 2 |
| ye3NrNrYOY | borderline_positive | false_accept_risk_missing_empirical_grounding | 3 | 2 | 0 | False | [] | [] | 3 |

## 解释

- 当前 hard-negative formation 不足以支撑直接 reject-side blocker，因此不能简单把 balanced 规则变成 accept。
- 如果要继续优化，应该定向检查 reject 样本是否存在未抽取的 empirical insufficiency、missing baseline、missing quantitative result 或 method-only support 风险。
