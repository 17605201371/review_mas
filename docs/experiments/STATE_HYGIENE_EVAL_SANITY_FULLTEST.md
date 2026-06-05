# 4B State Hygiene Quick Result

**输入结果**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`
**样本数**：39

## 1. Decision Health

| metric | value |
|---|---:|
| accuracy | 0.7692 |
| macro-F1 | 0.4348 |
| accept precision | 0.0000 |
| accept recall | 0.0000 |
| reject precision | 0.7692 |
| reject recall | 1.0000 |
| predicted accept | 0 |
| predicted reject/nonaccept | 39 |

## 2. Confusion Matrix

| item | count |
|---|---:|
| `gold_accept_pred_accept` | 0 |
| `gold_accept_pred_nonaccept` | 9 |
| `gold_reject_pred_accept` | 0 |
| `gold_reject_pred_nonaccept` | 30 |

## 3. Blocker Distribution

| blocker | samples |
|---|---:|
| `strong<2` | 28 |
| `unresolved>=6` | 18 |
| `critical>=1` | 14 |
| `major>0_blocks_accept` | 10 |
| `unresolved>3_blocks_accept` | 10 |
| `major>=2` | 6 |
| `conflicts>=4` | 1 |

## 4. Hygiene Totals

| metric | total |
|---|---:|
| `candidate_major` | 35 |
| `confirmed_major` | 1 |
| `conflict_count` | 48 |
| `grounded_flaw` | 28 |
| `meta_or_excerpt_flaw` | 4 |
| `stale_evidence_gap` | 31 |
| `ungrounded_flaw` | 24 |
| `unresolved_count` | 227 |
| `unsupported_with_2plus_strong` | 4 |
| `unsupported_with_strong_support` | 20 |

## 5. Group Metrics

### gold_accept

- **n**: 9
- **accept recall**: 0.0000
- **reject recall**: 0.0000
- **predicted_dist**: `{'reject': 9}`

### oracle_false_accept_reject

- **n**: 5
- **accept recall**: 0.0000
- **reject recall**: 1.0000
- **predicted_dist**: `{'reject': 5}`

### stable_reject_control

- **n**: 2
- **accept recall**: 0.0000
- **reject recall**: 1.0000
- **predicted_dist**: `{'reject': 2}`

### ungrouped

- **n**: 23
- **accept recall**: 0.0000
- **reject recall**: 1.0000
- **predicted_dist**: `{'reject': 23}`

