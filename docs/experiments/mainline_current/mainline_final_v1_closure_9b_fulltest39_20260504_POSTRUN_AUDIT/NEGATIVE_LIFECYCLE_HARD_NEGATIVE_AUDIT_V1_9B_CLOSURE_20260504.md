# NEGATIVE_LIFECYCLE_HARD_NEGATIVE_AUDIT_V1

## 结论

这份审计说明：raw negative burden 仍然很高，但其中相当一部分是 context limitation、targetless open question、stale gap 或 fallback/meta flaw，不能直接当作 paper-grounded reject blocker。正式推荐应继续使用 final-view lifecycle，而不是 raw unresolved/flaw count。

## Aggregate

| metric | value |
| --- | --- |
| rows | 39 |
| raw_unresolved_total | 269 |
| raw_gap_total | 110 |
| raw_flaw_total | 48 |
| raw_conflict_total | 73 |
| hygiene_open_unresolved_total | 0 |
| hygiene_gap_total | 52 |
| hygiene_conflict_total | 35 |

## Unresolved Categories

| category | count |
| --- | --- |
| context_limitation | 69 |
| targetless_open_question | 200 |

## Gap Categories

| category | count |
| --- | --- |
| open_gap | 68 |
| stale_gap_resolved_by_support | 42 |

## Flaw Categories

| category | count |
| --- | --- |
| fallback_or_meta_flaw | 43 |
| grounded_major_or_critical | 1 |
| ungrounded_candidate | 4 |

## Conflict Categories

| category | count |
| --- | --- |
| fallback_or_context_conflict | 53 |
| open_conflict | 20 |

## High Burden Cases

| paper_id | gold | view | real | empirical | raw_unresolved | raw_gap | raw_flaw | hygiene_open_unresolved | hygiene_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| a6SntIisgg | reject | borderline_insufficient | 2 | 0 | 9 | 6 | 2 | 0 | 2 |
| rEqETC88RY | reject | not_assessable_uncertain | 0 | 0 | 9 | 5 | 3 | 0 | 3 |
| ZHr0JajZfH | reject | not_assessable_uncertain | 0 | 0 | 10 | 5 | 1 | 0 | 4 |
| XyB4VvF01X | reject | borderline_insufficient | 2 | 2 | 10 | 3 | 2 | 0 | 1 |
| 2L7KQ4qbHi | reject | not_assessable_uncertain | 0 | 0 | 10 | 3 | 2 | 0 | 1 |
| WNxlJJIEVj | reject | borderline_insufficient | 1 | 0 | 7 | 5 | 2 | 0 | 2 |
| 9zEBK3E9bX | reject | borderline_positive | 3 | 3 | 10 | 3 | 1 | 0 | 1 |
| gzqrANCF4g | accept | reject_like | 1 | 1 | 10 | 2 | 2 | 0 | 1 |
| HPuLU6q7xq | reject | not_assessable_uncertain | 0 | 0 | 10 | 2 | 2 | 0 | 1 |
| XH3OiIhtvf | reject | not_assessable_uncertain | 0 | 0 | 10 | 2 | 2 | 0 | 1 |
| GE6iywJtsV | reject | not_assessable_uncertain | 0 | 0 | 10 | 2 | 1 | 0 | 1 |
| KOUAayk5Kx | reject | borderline_insufficient | 2 | 2 | 10 | 2 | 1 | 0 | 0 |

## 下一步

- 不应把 raw unresolved / gap / flaw count 直接接入 reject。
- 应继续在 final-view 中区分 context limitation、targetless unresolved、unverified hard-negative 与 grounded blocker。
- 若要提高 accept recovery，应优先提高 grounded hard-negative / criterion assessment 质量，而不是放宽 accept threshold。
