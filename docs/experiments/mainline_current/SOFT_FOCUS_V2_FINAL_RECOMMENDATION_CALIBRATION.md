# Soft Focus v2 Final Recommendation Calibration

| rule | accuracy | macro_f1 | accept_recall | reject_recall | pred_accept | false_accept_ids | recovered_accept_ids |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_current | 0.7436 | 0.4265 | 0.0 | 0.9667 | 1 | NnExMNiTHw |  |
| support_count_real_ge2 | 0.641 | 0.5293 | 0.3333 | 0.7333 | 11 | uOrfve3prk,9zEBK3E9bX,XyB4VvF01X,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 |
| support_quality_basic | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 9zEBK3E9bX,XyB4VvF01X,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 |
| method_plus_result | 0.7692 | 0.5237 | 0.1111 | 0.9667 | 2 | ZHr0JajZfH | LebzzClHYw |
| criterion_positive | 0.6667 | 0.5477 | 0.3333 | 0.7667 | 10 | 9zEBK3E9bX,XyB4VvF01X,GE6iywJtsV,NnExMNiTHw,QAgwFiIY4p,KOUAayk5Kx,ZHr0JajZfH | gzqrANCF4g,LebzzClHYw,BXY6fe7q31 |
| high_precision_criterion_quality | 0.7949 | 0.5412 | 0.1111 | 1.0 | 1 |  | LebzzClHYw |
