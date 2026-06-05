# Evidence Empirical Structuring v1 Compare

## 结论

- decision: `retain_for_next_fulltest_diagnostic`
- reason: strong empirical support increased without reducing rows_with_strong_empirical or empirical payload evidence.

## Aggregate comparison

| metric | observability baseline | empirical structuring v1 | delta |
| --- | ---: | ---: | ---: |
| avg_reward | 0.4338 | 0.426 | -0.0078 |
| evidence_turns | 83 | 85 | 2 |
| field_turns | 67 | 69 | 2 |
| raw_empirical_term_total | 239 | 336 | 97 |
| payload_empirical_evidence_total | 33 | 52 | 19 |
| payload_strong_empirical_total | 8 | 27 | 19 |
| rows_with_payload_empirical | 14 | 16 | 2 |
| rows_with_strong_empirical | 6 | 13 | 7 |

## Status counts

| status | baseline | v1 | delta |
| --- | ---: | ---: | ---: |
| empirical_payload_without_strong_support | 20 | 16 | -4 |
| no_raw_empirical_signal | 13 | 10 | -3 |
| raw_empirical_no_payload_evidence | 19 | 17 | -2 |
| raw_empirical_payload_no_empirical_evidence | 8 | 0 | -8 |
| strong_empirical_payload_formed | 7 | 26 | 19 |

## Case table

| paper_id | baseline strong_emp | v1 strong_emp | baseline payload_emp | v1 payload_emp | baseline reward | v1 reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cWEfRkYj46 | 1 | 1 | 2 | 2 | 0.3987 | 0.3567 |
| xYzOkOGD96 | 0 | 0 | 3 | 5 | 0.7435 | 0.7379 |
| nrvoWOWcyg | 0 | 2 | 1 | 4 | 0.2035 | 0.1729 |
| bcHty5VvkQ | 0 | 3 | 5 | 6 | 0.5093 | 0.5065 |
| VEJzjAvaIy | 2 | 2 | 2 | 2 | 0.3283 | 0.3159 |
| k243qi7S50 | 0 | 0 | 3 | 2 | 0.6076 | 0.6292 |
| nrRkAAAufl | 0 | 1 | 3 | 3 | 0.2641 | 0.2786 |
| GSckuQMzBG | 1 | 3 | 2 | 4 | 0.5044 | 0.2820 |
| IdAyXxBud7 | 0 | 0 | 2 | 3 | 0.2271 | 0.2161 |
| JdWpIe70FL | 2 | 2 | 5 | 5 | 0.5718 | 0.5480 |
| pOq9vDIYev | 1 | 3 | 1 | 3 | 0.2583 | 0.3028 |
| YvWuac63bg | 0 | 3 | 2 | 3 | 0.6204 | 0.6593 |
| giU9fYGTND | 1 | 1 | 1 | 1 | 0.2587 | 0.3011 |
| qgyF6JVmar | 0 | 3 | 0 | 3 | 0.6678 | 0.6743 |
| cpGPPLLYYx | 0 | 1 | 1 | 3 | 0.2792 | 0.3333 |
| 77plFC53J5 | 0 | 2 | 0 | 3 | 0.4987 | 0.5017 |
