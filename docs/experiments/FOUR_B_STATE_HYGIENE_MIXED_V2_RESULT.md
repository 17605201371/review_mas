# 4B State Hygiene Mixed v2 Result

**输入结果**：`outputs/results_main/review_infer/p25_1_state_hygiene_mixed_v2.jsonl`
**样本数**：16

## 1. Decision Health

| metric | value |
|---|---:|
| accuracy | 0.5000 |
| macro-F1 | 0.3333 |
| accept precision | 0.0000 |
| accept recall | 0.0000 |
| reject precision | 0.5000 |
| reject recall | 1.0000 |
| predicted accept | 0 |
| predicted reject/nonaccept | 16 |

## 2. Confusion Matrix

| item | count |
|---|---:|
| `gold_accept_pred_accept` | 0 |
| `gold_accept_pred_nonaccept` | 8 |
| `gold_reject_pred_accept` | 0 |
| `gold_reject_pred_nonaccept` | 8 |

## 3. Blocker Distribution

| blocker | samples |
|---|---:|
| `unresolved>=6` | 15 |
| `strong<2` | 15 |
| `critical>=1` | 8 |
| `conflicts>=4` | 3 |
| `major>0_blocks_accept` | 1 |
| `unresolved>3_blocks_accept` | 1 |

## 4. Hygiene Totals

| metric | total |
|---|---:|
| `candidate_major` | 8 |
| `confirmed_major` | 0 |
| `conflict_count` | 39 |
| `grounded_flaw` | 6 |
| `meta_or_excerpt_flaw` | 2 |
| `stale_evidence_gap` | 1 |
| `ungrounded_flaw` | 11 |
| `unresolved_count` | 145 |
| `unsupported_with_2plus_strong` | 1 |
| `unsupported_with_strong_support` | 2 |

## 5. Group Metrics

### fresh_accept

- **n**: 8
- **accept recall**: 0.0000
- **reject recall**: 0.0000
- **predicted_dist**: `{'reject': 8}`

### fresh_reject

- **n**: 8
- **accept recall**: 0.0000
- **reject recall**: 1.0000
- **predicted_dist**: `{'reject': 8}`

