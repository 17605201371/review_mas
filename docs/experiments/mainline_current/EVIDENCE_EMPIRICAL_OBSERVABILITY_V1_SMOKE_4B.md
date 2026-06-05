# Evidence Empirical Observability v1 Smoke 4B

## 结论

- rows: `2`
- evidence_turns: `6`
- field_turns: `4`
- structuring_status_counts: `{'no_raw_empirical_signal': 1, 'raw_empirical_payload_no_empirical_evidence': 1, 'empirical_payload_without_strong_support': 1, 'strong_empirical_payload_formed': 1}`

## Case rows

| paper_id | final_decision | reward | status_counts |
| --- | --- | --- | --- |
| ye3NrNrYOY | reject | 0.5874 | {'no_raw_empirical_signal': 1, 'raw_empirical_payload_no_empirical_evidence': 1} |
| WNxlJJIEVj | reject | 0.5618 | {'empirical_payload_without_strong_support': 1, 'strong_empirical_payload_formed': 1} |

## 示例字段

| paper_id | turn | status | raw_empirical_terms | payload_empirical_evidence | strong_empirical |
| --- | ---: | --- | ---: | ---: | ---: |
| ye3NrNrYOY | 2 | no_raw_empirical_signal | 0 | 0 | 0 |
| ye3NrNrYOY | 4 | raw_empirical_payload_no_empirical_evidence | 2 | 0 | 0 |
| WNxlJJIEVj | 2 | empirical_payload_without_strong_support | 2 | 1 | 0 |
