# 4B State Hygiene Quick Result

**输入结果**：`outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
**样本数**：16

## 1. Decision Health

| metric | value |
|---|---:|
| accuracy | 0.4375 |
| macro-F1 | 0.3043 |
| accept precision | 0.0000 |
| accept recall | 0.0000 |
| reject precision | 0.4375 |
| reject recall | 1.0000 |
| predicted accept | 0 |
| predicted reject/nonaccept | 16 |

## 2. Confusion Matrix

| item | count |
|---|---:|
| `gold_accept_pred_accept` | 0 |
| `gold_accept_pred_nonaccept` | 9 |
| `gold_reject_pred_accept` | 0 |
| `gold_reject_pred_nonaccept` | 7 |

## 3. Blocker Distribution

| blocker | samples |
|---|---:|
| `unresolved>=6` | 14 |
| `strong<2` | 12 |
| `critical>=1` | 8 |
| `unresolved>3_blocks_accept` | 4 |
| `major>0_blocks_accept` | 2 |
| `major>=2` | 2 |

## 4. Hygiene Totals

| metric | total |
|---|---:|
| `candidate_major` | 11 |
| `confirmed_major` | 0 |
| `conflict_count` | 27 |
| `grounded_flaw` | 7 |
| `meta_or_excerpt_flaw` | 1 |
| `stale_evidence_gap` | 8 |
| `ungrounded_flaw` | 14 |
| `unresolved_count` | 126 |
| `unsupported_with_2plus_strong` | 2 |
| `unsupported_with_strong_support` | 11 |

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

## 6. Interpretation

- **4B focus run 仍然全 reject**：16 条样本预测分布为 `{reject: 16}`，9 条 gold accept 的 accept recall 仍为 0。这说明当前问题不是换大/小模型能直接解释的模型尺寸问题，而是 ReviewState 到 final decision 的接口仍然有结构性 reject bias。
- **主要 blocker 仍在 final decision 输入侧**：`unresolved>=6` 覆盖 14/16，`strong<2` 覆盖 12/16，`critical>=1` 覆盖 8/16。即使 claim/evidence hygiene 有局部修正空间，只要 unresolved/flaw/strong-support 接口不变，final decision 仍会被压成 reject。
- **state hygiene 污染仍然真实存在**：`unsupported_with_strong_support=11`、`stale_evidence_gap=8`、`ungrounded_flaw=14`、`unresolved_count=126`。这些指标支持“先清理状态一致性”的方向，但不能证明简单 hygiene cleanup 会恢复 accept recall。
- **runtime fix 不能直接上 controller**：这轮验证的价值是确认下一步应围绕 state hygiene 与 final decision interface 做离线校准，而不是继续追加 recovery/sticky/throttle controller。

## 7. Decision

本轮不建议直接实现新的 recovery controller，也不建议把 accept/reject accuracy 作为主指标。下一步应先做 4B/offline 的 **Decision Interface Hygiene Simulation**：在不重跑模型的前提下，分别测试 unresolved lifecycle、candidate flaw weighting、grounded flaw filtering、strong support/claim status reconciliation 对 final decision blocker 的影响。只有当离线规则能减少 reject collapse 且不破坏 stable reject controls 时，再进入最小 runtime state hygiene fix。

