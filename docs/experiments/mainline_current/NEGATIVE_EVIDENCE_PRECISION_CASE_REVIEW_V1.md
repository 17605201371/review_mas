# Negative Evidence Precision Case Review v1

## 结论

v1.2 形成的 trusted blocker 中，只有一部分是真正可作为下一轮候选的 paper-grounded flaw；大量 blocker 实际是 context-limited 或 abstract-only missing support，不能进入 final decision。

## Label Summary

| label | count |
| --- | ---: |
| candidate_paper_grounded_flaw | 5 |
| context_limited_not_assessable | 2 |
| insufficient_anchor | 1 |

## By Tag

| tag | label | count |
| --- | --- | ---: |
| false_accept | candidate_paper_grounded_flaw | 5 |
| false_accept | insufficient_anchor | 1 |
| false_accept | context_limited_not_assessable | 1 |
| recovered_accept | context_limited_not_assessable | 1 |

## Case Table

| paper_id | gold | tag | kind | criterion | label | strict | anchor | evidence_or_rationale |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| WLgbjzKJkk | reject | false_accept | negative_evidence | empirical | insufficient_anchor | 0 | Abstract | Abstract lacks quantitative results or architectural details for CO-MOT's efficacy. |
| WpXq5n8yLb | reject | false_accept | negative_evidence | empirical | context_limited_not_assessable | 0 | Abstract | Abstract cuts off before showing comparative table for 'state-of-the-art' claim. |
| WpXq5n8yLb | reject | false_accept | flaw_confirmation | empirical | candidate_paper_grounded_flaw | 0 | Abstract | Abstract lacks concrete table/figure to substantiate 'state-of-the-art' claim. |
| aTBE70xiFw | reject | false_accept | flaw_confirmation | empirical | candidate_paper_grounded_flaw | 1 | Results section | No experimental validation for cryo-EM projections. |
| kam84eEmub | reject | false_accept | negative_evidence | empirical | candidate_paper_grounded_flaw | 1 | Results section | No quantitative metrics or comparison tables provided to validate 'realistic' DAG generation quality. |
| kam84eEmub | reject | false_accept | flaw_confirmation | empirical | candidate_paper_grounded_flaw | 1 | Results section | Abstract claims realism but Results lack validation metrics. |
| ye3NrNrYOY | reject | false_accept | negative_evidence | empirical | candidate_paper_grounded_flaw | 0 | abstract | No experimental results or performance metrics are provided to support the claim of learning a temporal causal mechanism. |
| KI9NqjLVDT | accept | recovered_accept | negative_evidence | empirical | context_limited_not_assessable | 0 | Abstract cuts off mid-sentence | No quantitative results or benchmark datasets visible to verify 'on par with or outperforms' claim. |

## v2 规则建议

1. `context_limited_not_assessable` 必须进入 not-assessable，不得作为 blocker。
2. `abstract_only_missing_support` 只能作为 weak candidate，除非同时有 result/table/experiment anchor。
3. `candidate_paper_grounded_flaw` 需要 paper anchor 含 result/table/experiment/baseline/metric/ablation，并且 claim_id 为真实 claim。
4. `insufficient_anchor` 进入 report warning，不进入 final decision。
