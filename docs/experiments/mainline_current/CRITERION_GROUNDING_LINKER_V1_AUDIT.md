# Criterion Grounding Linker v1 Audit

Input: `outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl`
Rows: `39`

| criterion | covered | coverage_rate | state_grounded | grounded_rate | positive_grounded | negative_grounded | not_assessable | report_only | meta_leakage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| novelty_originality | 6 | 0.1538 | 10 | 0.2564 | 10 | 0 | 30 | 0 | 3 |
| significance_contribution | 35 | 0.8974 | 7 | 0.1795 | 7 | 0 | 13 | 20 | 31 |
| technical_soundness | 34 | 0.8718 | 13 | 0.3333 | 10 | 4 | 11 | 14 | 28 |
| empirical_adequacy | 19 | 0.4872 | 7 | 0.1795 | 7 | 2 | 33 | 0 | 14 |
| clarity_reproducibility | 7 | 0.1795 | 15 | 0.3846 | 10 | 9 | 25 | 0 | 5 |

## 汇总

- avg covered criteria/report: `2.59`
- avg state-grounded criteria/report: `1.333`
- report-only criterion mentions: `34`
