# Evidence Empirical Observability v1 Sanity

## 结果

- status: `pass`
- failed_checks: `[]`
- observation_chars: `1904`
- context_sources: `['abstract']`

## Turn log subset

```json
{
  "evidence_context_contains_empirical_terms": true,
  "evidence_context_empirical_term_count": 7,
  "evidence_raw_contains_empirical_terms": true,
  "evidence_raw_empirical_term_count": 5,
  "evidence_payload_empirical_evidence_count": 1,
  "evidence_payload_strong_empirical_count": 1,
  "evidence_empirical_structuring_status": "strong_empirical_payload_formed"
}
```

## 结论

该 sanity 只验证字段能落入 turn log，不代表模型效果提升。下一轮如果跑 4B/9B 样本，应先看 `evidence_empirical_structuring_status` 的分布，再决定是否做 empirical-targeted context/pass。
