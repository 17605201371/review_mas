# P31.6 Readiness Status

- P32 entry ready: **False**
- next action: Run a fresh P31.6 full20 with scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest, then fill and validate the manual audit template.

## Latest Run

- run base: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260702_131007`
- rows: `20`
- running: `False`
- pid: `46241`

## Entry Gate

- path: `P31_6_CRITORIGIN_RECOMPUTE_163953_ENTRY_GATE_WITH_MANUAL_AUDIT.json`
- machine gate: **FAIL**
- manual gate: **FAIL**
- blocking issues:
  - critique_payload_verified_cluster_count: actual 2, required >= 3
  - case_table_critique_origin_cluster_count: actual 2, required >= 3
  - manual_audit_status: actual FAIL, required PASS
  - manual_critique_origin_A_B_clusters: actual 2, required >= 3

## Key Metrics

| metric | value |
|---|---:|
| `verified_review_issue_count` | 19 |
| `verified_review_issue_cluster_recomputed_count` | 16 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 16 |
| `critique_payload_verified_cluster_count` | 2 |
| `verified_review_issue_cluster_origin_critique_payload_count` | 2 |
| `mark_contested_commit_count` | 5 |

## Manual Audit

- validation: `P31_6_CRITORIGIN_RECOMPUTE_163953_MANUAL_AUDIT_VALIDATION.json`
- status: **FAIL**
- manual A/B clusters: `2`
- manual D clusters: `0`
- unfilled clusters: `0`

## API Preflight

- status: `ok`

## Command

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
