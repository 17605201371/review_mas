# Evidence Lineage Support View v1 Results

## Aggregate

- `rows`: 39
- `lineage_real_strong_total`: 28
- `lineage_nonabstract_total`: 16
- `lineage_empirical_total`: 7
- `lineage_method_total`: 9
- `rows_with_2plus_lineage_real_strong`: 9
- `rows_with_2plus_nonabstract_independent`: 2
- `rows_with_method_plus_empirical`: 0
- `final_real_strong_total`: 9

## Decision Simulations

| simulation | accuracy | macro_f1 | accept_recall | reject_recall | predicted_accept | borderline | false_accept_ids | recovered_accept_ids |
|---|---:|---:|---:|---:|---:|---:|---|---|
| current_pred | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 |  |  |
| sim_lineage_support | 0.5385 | 0.35 | 0.0 | 0.7 | 9 | 0 | ye3NrNrYOY,7Dub7UXTXN,cklg91aPGk,HPuLU6q7xq,TPAj63ax4Y,XH3OiIhtvf,ZHr0JajZfH,N0isTh3rml,aRxLDcxFcL |  |
| sim_nonabstract_independent | 0.7179 | 0.4179 | 0.0 | 0.9333 | 2 | 0 | cklg91aPGk,aRxLDcxFcL |  |
| sim_conservative | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | 0 | cklg91aPGk |  |
| sim_borderline_strict | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 11 |  |  |
| sim_borderline_lenient | 0.4872 | 0.3276 | 0.0 | 0.6333 | 11 | 11 | uOrfve3prk,7Dub7UXTXN,NnExMNiTHw,cklg91aPGk,QAgwFiIY4p,mHv6wcBb0z,xUe1YqEgd6,XH3OiIhtvf,ZHr0JajZfH,9JRsAj3ymy,N0isTh3rml |  |
