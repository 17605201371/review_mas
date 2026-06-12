# Post4tasks Case Anomaly Audit v1

- input: `mimo_v25_hygienefilter3_mt7_smoke8_b4w2_api2_20260612_160109.jsonl`
- schema: `post4tasks_case_anomaly_audit_v1_20260611`
- papers: `8`

## Metric Before/After Recompute

| metric | stored | recomputed |
| --- | --- | --- |
| state_contamination_count | 0 | 0 |
| contamination_evidence_misbinding | 0 | 0 |
| open_conflict_count | 0 | 0 |
| negative_semantic_anchor_conflict_count | 0 | 0 |
| invalid_negative_evidence_id_count_legacy | 0 | 0 |
| negative_evidence_semantic_rejected_count | 1 | 1 |
| negative_evidence_candidate_count | 12 | 12 |
| verified_negative_flaw_count | 12 | 12 |
| verified_actionable_negative_flaw_count | 7 | 7 |
| potential_concern_count | 7 | 7 |

## P0-1 Open Conflict Cases

| paper_id | claim_id | flaw_id | conflict_id | negative_evidence_id | why_conflict_remained_open |
| --- | --- | --- | --- | --- | --- |

## P0-2 Evidence Misbinding Cases

| paper_id | claim_id | flaw_id | evidence_id | why_misbinding_counted |
| --- | --- | --- | --- | --- |

## P0-3 Negative Semantic Anchor Cases

| paper_id | claim_id | flaw_id | negative_evidence_id | semantic_label | final_view_after |
| --- | --- | --- | --- | --- | --- |
| WLgbjzKJkk | claim-paper-fallback-3 | flaw-negative-quote-bank-quote-table-or-figure-3 | evidence-negative-quote-bank-quote-table-or-figure-3-4 | semantic_mismatch | {'negative_semantic_anchor_conflict_count': 0, 'negative_evidence_semantic_rejected_count': 1, 'verified_negative_flaw_count': 2} |

## P0-4 Verified Negative Flaw Mapping

- all_negative_evidence_ids: `12`
- all_verified_negative_flaw_ids: `12`
- duplicate_negative_evidence_ids: `0`
- legacy_negative_evidence_ids: `0`
- shared_negative_evidence_ids: `7`

## Interpretation

- Stored smoke8 anomalies are attributable to stale support-only conflict accounting, handled semantic negative-anchor rejection, and inactive duplicate flaw counting.
- Recomputed metrics should be used to decide whether a runtime rerun is necessary; this script does not mutate the original run.
