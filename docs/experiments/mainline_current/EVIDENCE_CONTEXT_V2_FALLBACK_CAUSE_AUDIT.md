# Evidence Context v2 Fallback Cause Audit

## 结论

v2 的 fallback 激增主要不是由 fallback claim binding 造成，而是更复杂/更长的 Evidence observation 使 fallback evidence payload 更频繁出现。它同时没有提高 real-support payload rate，因此不应继续直接加长 context 或堆 prompt。

## Aggregate Compare

| metric | baseline | context v2 | delta |
|---|---:|---:|---:|
| `evidence_turns` | 92 | 92 | +0 |
| `evidence_payloads` | 77 | 79 | +2 |
| `fallback_payloads` | 2 | 17 | +15 |
| `fallback_payload_rate` | 0.0217 | 0.1848 | +0.1630 |
| `payloads_with_real_support` | 34 | 18 | -16 |
| `payload_real_support_rate` | 0.4416 | 0.2278 | -0.2137 |
| `avg_context_chars` | 2220.5761 | 2592.4457 | +371.8696 |
| `visible_method_rate` | 0.1739 | 0.4783 | +0.3043 |
| `visible_results_rate` | 0.6304 | 0.4457 | -0.1848 |
| `visible_table_or_figure_rate` | 0.7391 | 0.7826 | +0.0435 |
| `broad_target_turn_rate` | 0.8913 | 0.9565 | +0.0652 |

## Fallback Reason Breakdown

| reason | baseline | context v2 |
|---|---:|---:|
| `fallback_evidence_id` | 2 | 17 |

## Per-Case Deltas

| paper_id | fallback delta | broad target delta | real-support payload delta |
|---|---:|---:|---:|
| xYzOkOGD96 | 5 | 4 | -2 |
| GSckuQMzBG | 3 | 0 | -2 |
| nrRkAAAufl | 1 | 0 | -4 |
| k243qi7S50 | 1 | 3 | -2 |
| nrvoWOWcyg | 1 | 3 | -2 |
| 77plFC53J5 | 1 | 2 | -1 |
| JdWpIe70FL | 1 | 2 | 0 |
| bcHty5VvkQ | 1 | -1 | 0 |
| pOq9vDIYev | 1 | 6 | 0 |
| qgyF6JVmar | 1 | -1 | 0 |
| VEJzjAvaIy | 0 | 2 | -2 |
| cpGPPLLYYx | 0 | -5 | -1 |
| YvWuac63bg | 0 | -2 | 1 |
| IdAyXxBud7 | -1 | -7 | -1 |

## Context v2 Fallback Examples

| paper_id | turn | reason | context chars | sources | target count | fallback ids |
|---|---:|---|---:|---|---:|---|
| xYzOkOGD96 | 1 | fallback_evidence_id | 2124 | abstract,table_or_figure,conclusion | 3 | evidence-fallback-1 |
| xYzOkOGD96 | 4 | fallback_evidence_id | 2124 | abstract,table_or_figure,conclusion | 3 | evidence-fallback-2 |
| xYzOkOGD96 | 5 | fallback_evidence_id | 2124 | abstract,table_or_figure,conclusion | 3 | evidence-fallback-3 |
| xYzOkOGD96 | 6 | fallback_evidence_id | 2124 | abstract,table_or_figure,conclusion | 4 | evidence-fallback-4 |
| xYzOkOGD96 | 7 | fallback_evidence_id | 2124 | abstract,table_or_figure,conclusion | 4 | evidence-fallback-5 |
| nrvoWOWcyg | 1 | fallback_evidence_id | 2681 | abstract,results,table_or_figure | 3 | evidence-fallback-1 |
| bcHty5VvkQ | 6 | fallback_evidence_id | 3000 | abstract,method,table_or_figure,conclusion | 3 | evidence-fallback-3 |
| k243qi7S50 | 1 | fallback_evidence_id | 2204 | abstract,table_or_figure,conclusion | 3 | evidence-fallback-1 |
| nrRkAAAufl | 1 | fallback_evidence_id | 2482 | abstract,method,table_or_figure | 3 | evidence-fallback-1 |
| nrRkAAAufl | 3 | fallback_evidence_id | 2482 | abstract,method,table_or_figure | 3 | evidence-fallback-2 |
| GSckuQMzBG | 1 | fallback_evidence_id | 3000 | abstract,method,results,conclusion | 3 | evidence-fallback-1 |
| GSckuQMzBG | 3 | fallback_evidence_id | 3000 | abstract,method,results,conclusion | 3 | evidence-fallback-2 |

## 下一步

不要直接进入 Evidence Context v3。更合理的下一刀是继续保持 v1 context，围绕 Evidence Agent 输出结构做小修：降低 fallback payload 的触发概率、保留现有 binding 约束，并优先在 2-5 条 accept-side case 上做快速验证。
