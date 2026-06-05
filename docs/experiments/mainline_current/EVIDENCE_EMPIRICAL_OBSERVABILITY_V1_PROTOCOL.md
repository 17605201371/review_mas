# Evidence Empirical Context & Raw Output Observability v1

## 目标

本轮只补观测字段，不改 Evidence Agent 输入、不改 prompt、不改 fallback、不改 binding、不改 final decision。目标是把 empirical/result/table support 的断点拆成四层：

1. Evidence context 是否包含 empirical/table/method 线索。
2. Evidence Agent raw output 是否提到 empirical/table 线索。
3. 解析后的 payload 是否形成 empirical evidence item。
4. payload 是否形成 supports + strong 的 empirical evidence。

## 新增字段

- `evidence_context_contains_empirical_terms`
- `evidence_context_empirical_term_count`
- `evidence_context_table_or_figure_term_count`
- `evidence_context_method_term_count`
- `evidence_empirical_observability_mode`
- `evidence_raw_contains_empirical_terms`
- `evidence_raw_contains_table_or_figure_terms`
- `evidence_raw_empirical_term_count`
- `evidence_raw_negative_empirical_term_count`
- `evidence_payload_evidence_count`
- `evidence_payload_empirical_evidence_count`
- `evidence_payload_table_or_figure_count`
- `evidence_payload_method_evidence_count`
- `evidence_payload_strong_empirical_count`
- `evidence_payload_support_empirical_count`
- `evidence_payload_has_empirical_evidence`
- `evidence_empirical_structuring_status`

## 边界

这些字段只用于 turn log / runner trace 诊断。它们不改变 worker payload，不改变 ReviewState merge，不改变 recommendation policy。
