# Negative Evidence Formation Diagnostic Subset

## 定位

该子集用于下一轮小样本 negative evidence / flaw confirmation pass，只包含 9B dry-run 中 criterion Sim4 的 false accept 和 recovered accept。

| paper_id | gold | sim4 | tag | trusted | weak | oracle_hard_criteria | real_strong | non_abs | next_action |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| NnExMNiTHw | reject | accept_like | false_accept | 0 | 1 | clarity,empirical,significance,soundness,unspecified | 3 | 1 | target_negative_evidence_pass |
| WLgbjzKJkk | reject | accept_like | false_accept | 0 | 1 | empirical,unspecified | 2 | 1 | target_negative_evidence_pass |
| WpXq5n8yLb | reject | accept_like | false_accept | 0 | 0 | clarity,empirical,significance,unspecified | 2 | 2 | target_negative_evidence_pass |
| a6SntIisgg | reject | accept_like | false_accept | 0 | 1 | clarity,empirical,soundness,unspecified | 2 | 2 | target_negative_evidence_pass |
| aTBE70xiFw | reject | accept_like | false_accept | 0 | 1 | clarity,empirical,novelty,significance,soundness,unspecified | 3 | 1 | target_negative_evidence_pass |
| kam84eEmub | reject | accept_like | false_accept | 0 | 0 | clarity,empirical,soundness,unspecified | 4 | 1 | target_negative_evidence_pass |
| ye3NrNrYOY | reject | accept_like | false_accept | 0 | 1 | empirical,unspecified | 3 | 2 | target_negative_evidence_pass |
| 1HCN4pjTb4 | accept | accept_like | recovered_accept | 0 | 1 | clarity,novelty,significance,soundness,unspecified | 3 | 1 | protect_with_discriminative_confirmation |
| BXY6fe7q31 | accept | accept_like | recovered_accept | 0 | 0 | clarity,empirical,unspecified | 2 | 1 | protect_with_discriminative_confirmation |
| KI9NqjLVDT | accept | accept_like | recovered_accept | 1 | 0 | clarity,novelty,significance,soundness,unspecified | 2 | 2 | inspect_trusted_blocker_precision |
