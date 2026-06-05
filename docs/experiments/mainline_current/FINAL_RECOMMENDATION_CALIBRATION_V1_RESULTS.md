# Final Recommendation Calibration v1 Results

## 4b_mainline_fulltest39

| rule | pred_accept | true_accept | false_accept | accept_precision | accept_recall | reject_recall | macro_f1 | accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |
| support_count_real_ge2 | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |
| sim4_accept_like | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |
| calibrated_balanced | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |
| calibrated_high_precision | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |

### Three-way view

| label | count |
| --- | --- |
| borderline_insufficient | 3 |
| not_assessable | 8 |
| reject_like | 28 |

### 推荐读法

- high precision: recovered `0` accept, false accept `0`。
- balanced: recovered `0` accept, false accept `0`。
- 如果 balanced 比 high precision 多出的样本含 false accept，应作为 `borderline_positive`，不直接映射 accept。

## 9b_fulltest39_dryrun

| rule | pred_accept | true_accept | false_accept | accept_precision | accept_recall | reject_recall | macro_f1 | accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_runtime | 0 | 0 | 0 | 0.0 | 0.0 | 1.0 | 0.4348 | 0.7692 |
| support_count_real_ge2 | 14 | 5 | 9 | 0.3571 | 0.5556 | 0.7 | 0.5992 | 0.6667 |
| sim4_accept_like | 10 | 3 | 7 | 0.3 | 0.3333 | 0.7667 | 0.5477 | 0.6667 |
| calibrated_balanced | 5 | 3 | 2 | 0.6 | 0.3333 | 0.9333 | 0.6518 | 0.7949 |
| calibrated_high_precision | 2 | 2 | 0 | 1.0 | 0.2222 | 1.0 | 0.6296 | 0.8205 |

### Three-way view

| label | count |
| --- | --- |
| accept_like | 2 |
| borderline_insufficient | 5 |
| borderline_positive | 3 |
| not_assessable | 22 |
| reject_like | 7 |

### 推荐读法

- high precision: recovered `2` accept, false accept `0`。
- balanced: recovered `3` accept, false accept `2`。
- 如果 balanced 比 high precision 多出的样本含 false accept，应作为 `borderline_positive`，不直接映射 accept。
