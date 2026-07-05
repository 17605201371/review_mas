# P31.6 Readiness Status

- P32 entry ready: **False**
- next action: Run a fresh P31.6 full20 with scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest, then fill and validate the manual audit template.

## Latest Run

- run base: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_232528`
- rows: `20`
- running: `False`
- pid: `22187`

## Entry Gate

- path: `P32_CLEAN_R1_20260705_232527_ENTRY_GATE_AUDIT.json`
- machine gate: **PASS**
- manual gate: **REQUIRED**

## Key Metrics

| metric | value |
|---|---:|
| `verified_review_issue_count` | 24 |
| `verified_review_issue_cluster_recomputed_count` | 17 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 17 |
| `critique_payload_verified_cluster_count` | 6 |
| `candidate_menu_item_verified_count` | 6 |
| `candidate_menu_item_any_origin_verified_count` |  |
| `critique_only_verified_cluster_count` |  |
| `verified_review_issue_cluster_origin_critique_payload_count` | 4 |
| `mark_contested_commit_count` | 20 |

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
