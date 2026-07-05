# P31.6 Readiness Status

- P32 entry ready: **True**
- next action: P31.6 gate appears ready for P32 review; verify manual audit provenance before entering P32.

## Latest Run

- run base: `p31_30_bridge_guard_critique5_20260705_193123`
- rows: `5`
- running: `False`
- pid: ``

## Entry Gate

- path: `P31_30_BRIDGE_GUARD_CRITIQUE5_20260705_193123_ENTRY_GATE_AUDIT.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Key Metrics

| metric | value |
|---|---:|
| `verified_review_issue_count` | 6 |
| `verified_review_issue_cluster_recomputed_count` | 5 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 5 |
| `critique_payload_verified_cluster_count` | 4 |
| `candidate_menu_item_verified_count` | 4 |
| `candidate_menu_item_any_origin_verified_count` |  |
| `critique_only_verified_cluster_count` |  |
| `verified_review_issue_cluster_origin_critique_payload_count` | 3 |
| `mark_contested_commit_count` | 5 |

## Manual Audit

- validation: `P31_30_BRIDGE_GUARD_CRITIQUE5_ONLY_MANUAL_AUDIT_VALIDATION_20260705_193123.json`
- status: **PASS**
- manual A/B clusters: `4`
- manual D clusters: `0`
- unfilled clusters: `0`

## API Preflight

- status: `not_run`

## Command

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
