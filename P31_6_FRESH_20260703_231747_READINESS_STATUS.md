# P31.6 Readiness Status

- P32 entry ready: **False**
- next action: Run a fresh P31.6 full20 with scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest, then fill and validate the manual audit template.

## Latest Run

- run base: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok1536_20260703_231747`
- rows: `20`
- running: `False`
- pid: `4957`

## Entry Gate

- path: `P31_6_FRESH_20260703_231747_ENTRY_GATE_AUDIT.json`
- machine gate: **FAIL**
- manual gate: **REQUIRED**
- blocking issues:
  - critique_payload_verified_cluster_count: actual 0, required >= 3
  - candidate_menu_item_verified_count: actual 0, required >= 2
  - case_table_critique_origin_cluster_count: actual 0, required >= 3

## Key Metrics

| metric | value |
|---|---:|
| `verified_review_issue_count` | 16 |
| `verified_review_issue_cluster_recomputed_count` | 11 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 11 |
| `critique_payload_verified_cluster_count` | 0 |
| `candidate_menu_item_verified_count` | 0 |
| `candidate_menu_item_any_origin_verified_count` |  |
| `critique_only_verified_cluster_count` |  |
| `verified_review_issue_cluster_origin_critique_payload_count` | 0 |
| `mark_contested_commit_count` | 9 |

## Manual Audit

- validation: ``
- status: ****
- manual A/B clusters: ``
- manual D clusters: ``
- unfilled clusters: ``

## API Preflight

- status: `not_run`

## Command

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
