# Soft Focus v2 Final Recommendation Calibration

| rule | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_current | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 |  |  |
| support_count_real_ge2 | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | uOrfve3prk,9zEBK3E9bX,QAgwFiIY4p,TPAj63ax4Y,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 |
| support_quality_basic | 0.7179 | 0.546 | 0.2222 | 0.8667 | 6 | 9zEBK3E9bX,QAgwFiIY4p,TPAj63ax4Y,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 |
| method_plus_result | 0.7436 | 0.5076 | 0.1111 | 0.9333 | 3 | TPAj63ax4Y,ZHr0JajZfH | LebzzClHYw |
| criterion_positive | 0.7436 | 0.5647 | 0.2222 | 0.9 | 5 | 9zEBK3E9bX,TPAj63ax4Y,ZHr0JajZfH | LebzzClHYw,BXY6fe7q31 |
| high_precision_criterion_quality | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 |  |  |
