# P25.1 Commit Throughput

## 9B Expanded Recovery-Relevant Rows
| Metric | 9B main |
| --- | ---: |
| recovery_relevant_count | 24 |
| recovery_triggered_count | 13 |
| recovery_patch_mode_entered_count | 13 |
| patch_emitted_count | 11 |
| patch_validated_count | 13 |
| patch_committed_count | 7 |

## 9B Expanded Rates
| Metric | 9B main |
| --- | ---: |
| recovery_relevant_to_trigger_rate | 0.5417 |
| trigger_to_patch_mode_rate | 1.0 |
| patch_mode_to_emission_rate | 0.8462 |
| emission_to_validation_rate | 1.1818 |
| validation_to_commit_rate | 0.5385 |

## Fixed Reference Compare (4B vs 9B)
| Metric | 4B reference | 9B reference |
| --- | ---: | ---: |
| recovery_relevant_count | 8 | 8 |
| recovery_triggered_count | 6 | 6 |
| recovery_patch_mode_entered_count | 6 | 6 |
| patch_emitted_count | 6 | 6 |
| patch_validated_count | 6 | 6 |
| patch_committed_count | 2 | 4 |

## Fixed Reference Rates
| Metric | 4B reference | 9B reference |
| --- | ---: | ---: |
| recovery_relevant_to_trigger_rate | 0.75 | 0.75 |
| trigger_to_patch_mode_rate | 1.0 | 1.0 |
| patch_mode_to_emission_rate | 1.0 | 1.0 |
| emission_to_validation_rate | 1.0 | 1.0 |
| validation_to_commit_rate | 0.3333 | 0.6667 |

- note: `patch_validated_count` still includes blocked-but-validated recovery turns, so the main quality read should stay anchored on `NO_EFFECT_PATCH`, `patch_committed_count`, and real state changes.
