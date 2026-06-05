# Final-View Invalid Binding Filter v1 Simulation

| mapping | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept | true_accept |
| --- | --- | --- | --- | --- | --- | --- | --- |
| strict_borderline_as_reject | 0.7436 | 0.5076 | 0.1111 | 0.9333 | 3 | 2 | 1 |
| lenient_borderline_as_accept | 0.641 | 0.4944 | 0.2222 | 0.7667 | 9 | 7 | 2 |

## Aggregate

| metric | value |
| --- | --- |
| rows | 39 |
| total_strong_support | 14 |
| valid_real_strong_support | 14 |
| invalid_bound_strong_support | 0 |
| fallback_bound_strong_support | 0 |
| unbound_strong_support | 0 |
| rows_with_invalid_bound_evidence | 9 |
| rows_with_valid_2plus_support | 4 |
| gold_accept_with_valid_2plus_support | 1 |
