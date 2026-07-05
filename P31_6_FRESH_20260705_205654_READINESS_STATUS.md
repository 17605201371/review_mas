# P31.6 Readiness Status

- P32 entry ready: **True**
- next action: P31.6 gate appears ready for P32 review; verify manual audit provenance before entering P32.

## Latest Run

- run base: `mimo_v25_negqty_recoverycap_guard3_qhyg_targetneg_freeformrevneg_reviewissuebundle_hardneg20_mt7_b4w2_api4_r8t600_tok2048_20260705_205654`
- rows: `20`
- running: `False`
- pid: `69809`

## Entry Gate

- path: `P31_6_FRESH_20260705_205654_ENTRY_GATE_AUDIT.json`
- machine gate: **PASS**
- manual gate: **PASS**

## Key Metrics

| metric | value |
|---|---:|
| `verified_review_issue_count` | 10 |
| `verified_review_issue_cluster_recomputed_count` | 6 |
| `quote_duplicate_merged_verified_review_issue_cluster_count` | 6 |
| `critique_payload_verified_cluster_count` | 6 |
| `candidate_menu_item_verified_count` | 6 |
| `candidate_menu_item_any_origin_verified_count` |  |
| `critique_only_verified_cluster_count` |  |
| `verified_review_issue_cluster_origin_critique_payload_count` | 4 |
| `mark_contested_commit_count` | 16 |

## Manual Audit

- validation: `P31_6_FRESH_20260705_205654_MANUAL_AUDIT_VALIDATION.json`
- status: **PASS**
- manual A/B clusters: `6`
- manual D clusters: `0`
- unfilled clusters: `0`

## API Preflight

- status: `not_run`

## Command

```bash
scripts/p31_6_full20_pipeline.sh --launch --wait --update-latest
```
