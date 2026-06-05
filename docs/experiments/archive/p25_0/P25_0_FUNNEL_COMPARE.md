# P25.0 Funnel Compare

## Recovery-Relevant Rows
| Metric | 4B | 9B |
| --- | ---: | ---: |
| recovery_relevant_count | 8 | 8 |
| recovery_triggered_count | 6 | 6 |
| recovery_patch_mode_entered_count | 6 | 6 |
| patch_emitted_count | 5 | 6 |
| patch_validated_count | 6 | 6 |
| patch_committed_count | 3 | 4 |

## Recovery-Relevant Rates
| Metric | 4B | 9B |
| --- | ---: | ---: |
| recovery_relevant_to_trigger_rate | 0.75 | 0.75 |
| trigger_to_patch_mode_rate | 1.0 | 1.0 |
| patch_mode_to_emission_rate | 0.8333 | 1.0 |
| emission_to_validation_rate | 1.2 | 1.0 |
| validation_to_commit_rate | 0.5 | 0.6667 |

## Historical Sentinel Rows
| Metric | 4B | 9B |
| --- | ---: | ---: |
| recovery_relevant_count | 2 | 2 |
| recovery_triggered_count | 1 | 0 |
| recovery_patch_mode_entered_count | 1 | 0 |
| patch_emitted_count | 0 | 0 |
| patch_validated_count | 1 | 0 |
| patch_committed_count | 0 | 0 |

- note: `patch_validated_count` currently includes blocked-but-validated recovery turns, so `emission_to_validation_rate` can exceed 1 and should not be used as the primary quality signal.
