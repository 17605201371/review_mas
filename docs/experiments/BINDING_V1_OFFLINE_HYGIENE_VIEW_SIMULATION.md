# Binding v1 Offline Hygiene View Simulation
Input: `outputs/results_main/review_infer/evidence_binding_v1_mixed16.jsonl`. This is an offline derived-view simulation only: no model rerun and no live state mutation.
## Summary
- original_labeled_rows: 16
- original_accuracy: 0.5
- original_accept_recall: 0.0
- original_reject_recall: 1.0
- original_macro_f1: 0.3333333333333333
- original_predicted_accept_count: 0
- original_false_accept_ids: []
- original_recovered_accept_ids: []
- derived_labeled_rows: 16
- derived_accuracy: 0.6875
- derived_accept_recall: 0.375
- derived_reject_recall: 1.0
- derived_macro_f1: 0.6536796536796536
- derived_predicted_accept_count: 3
- derived_false_accept_ids: []
- derived_recovered_accept_ids: ['VEJzjAvaIy', 'pOq9vDIYev', 'cpGPPLLYYx']

## Aggregate Hygiene Signals
- real_strong_support: 13
- stale_gap_count: 19
- kept_gap_count: 25
- meta_unresolved_count: 47
- paper_unresolved_count: 64
- stale_conflict_count: 17
- kept_conflict_count: 15
- flaw_major: 0
- flaw_critical: 1
- flaw_grounded: 1
- flaw_ungrounded: 14
- flaw_fallback: 3

## Decision
Offline hygiene is the right next diagnostic because runtime hygiene changed the trajectory and reduced positive support. This simulation isolates the final-view effect on the fixed Binding v1 state.
