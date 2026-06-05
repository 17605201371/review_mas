# Criterion Grounding Linker v1 Audit

Input: `WEBGPT_9B_FULLTEST39_RERUN_20260429.jsonl`
Rows: `39`

| criterion | covered | coverage_rate | state_grounded | grounded_rate | positive_grounded | negative_grounded | not_assessable | report_only | meta_leakage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| novelty_originality | 10 | 0.2564 | 10 | 0.2564 | 9 | 1 | 1 | 5 | 3 |
| significance_contribution | 36 | 0.9231 | 9 | 0.2308 | 9 | 0 | 1 | 28 | 2 |
| technical_soundness | 29 | 0.7436 | 7 | 0.1795 | 3 | 5 | 5 | 21 | 19 |
| empirical_adequacy | 28 | 0.7179 | 4 | 0.1026 | 2 | 2 | 2 | 24 | 3 |
| clarity_reproducibility | 10 | 0.2564 | 14 | 0.359 | 9 | 7 | 5 | 2 | 8 |

## 汇总

- avg covered criteria/report: `2.897`
- avg state-grounded criteria/report: `1.128`
- report-only criterion mentions: `80`
