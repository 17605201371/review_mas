# Support Quality Audit

| metric | value |
| --- | --- |
| rows | 16 |
| real_strong_support_total | 13 |
| non_abstract_support_total | 9 |
| empirical_support_total | 2 |
| method_support_total | 7 |
| table_or_figure_support_total | 2 |
| ablation_support_total | 0 |
| independent_support_group_total | 12 |
| claims_with_2plus_independent_support | 3 |
| claims_with_only_abstract_support | 3 |
| fallback_or_unbound_strong_support | 0 |

## Labels
| label | rows |
| --- | --- |
| no_real_strong_support | 10 |
| method_grounded_support | 3 |
| deep_empirical_or_ablation_support | 2 |
| abstract_only_support | 1 |

## Error Subsets
| subset | rows | non_abstract_avg | independent_group_avg | empirical_avg |
| --- | --- | --- | --- | --- |
| false_accept | 0 | 0.0 | 0.0 | 0.0 |
| false_reject | 8 | 1.0 | 1.375 | 0.25 |
| gold_accept_without_nonabstract | 4 | 0.0 | 0.5 | 0.0 |
