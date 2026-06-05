# Full-test State Hygiene Offline Simulation

**日期**：2026-04-25
**输入**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl`（39 样本）
**脚本**：`scripts/simulate_state_hygiene_decision.py`
**原则**：不改 runtime，不重跑模型，只检验 state hygiene 修复是否存在收益空间。

## 1. 总表

| variant | acc | macro-F1 | accept R | reject R | pred A | pred R | W/T/L | flips | recovered A | false A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_infer` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `A_reconcile_partial` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `A_reconcile_supported` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `B_stale_gap_cleanup` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `C_meta_excerpt_filter` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `D_candidate_half_weight` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `D_grounded_candidate_only` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `E_combo_partial_half` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `E_combo_supported_half` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `E_combo_strict_grounded` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `F_liberal_unresolved_cleanup` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `F_liberal_all_hygiene` | 0.7692 | 0.4348 | 0.0000 | 1.0000 | 0 | 39 | 0/39/0 | 0 | 0 | 0 |
| `G_oracle_no_candidates_no_unresolved` | 0.6923 | 0.5282 | 0.2222 | 0.8333 | 7 | 32 | 2/32/5 | 7 | 2 | 5 |

## 2. 关键翻转样本

### A_reconcile_partial

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### A_reconcile_supported

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### B_stale_gap_cleanup

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### C_meta_excerpt_filter

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### D_candidate_half_weight

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### D_grounded_candidate_only

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### E_combo_partial_half

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### E_combo_supported_half

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### E_combo_strict_grounded

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### F_liberal_unresolved_cleanup

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### F_liberal_all_hygiene

- **flipped_sample_ids**: `[]`
- **recovered_accept_ids**: `[]`
- **false_accept_ids**: `[]`

### G_oracle_no_candidates_no_unresolved

- **flipped_sample_ids**: `['hj323oR3rw', 'X41c4uB4k0', 'NnExMNiTHw', 'fGXyvmWpw6', 'TPAj63ax4Y', 'aTBE70xiFw', 'kam84eEmub']`
- **recovered_accept_ids**: `['hj323oR3rw', 'X41c4uB4k0']`
- **false_accept_ids**: `['NnExMNiTHw', 'fGXyvmWpw6', 'TPAj63ax4Y', 'aTBE70xiFw', 'kam84eEmub']`

## 3. Reject blocker 诊断

### baseline blockers

| blocker | samples |
|---|---:|
| `strong<2` | 28 |
| `unresolved>=6` | 18 |
| `critical>=1` | 14 |
| `major>0_blocks_accept` | 10 |
| `unresolved>3_blocks_accept` | 10 |
| `major>=2` | 6 |
| `conflicts>=4` | 1 |

### candidate half-weight blockers

| blocker | samples |
|---|---:|
| `strong<2` | 28 |
| `unresolved>=6` | 18 |
| `major>0_blocks_accept` | 10 |
| `unresolved>3_blocks_accept` | 10 |
| `critical>=1` | 3 |
| `conflicts>=4` | 1 |

### grounded candidate half-weight blockers

| blocker | samples |
|---|---:|
| `strong<2` | 28 |
| `unresolved>=6` | 18 |
| `unresolved>3_blocks_accept` | 10 |
| `major>0_blocks_accept` | 9 |
| `critical>=1` | 1 |
| `conflicts>=4` | 1 |

## 4. 初步结论

- **A-E/F hygiene 模拟全部 0 翻转**：Claim-Evidence Reconciliation、Stale Gap Cleanup、Meta/Excerpt Filtering、Candidate 降权及其组合，都无法单独突破当前 final decision 的 reject 锁。
- **原因**：当前 `infer_final_decision` 不直接读取 claim status 或 `evidence_gaps`，只读取 flaws、open unresolved、conflicts 和全局 strong support；并且 accept 条件要求 `strong_support >= 2`、`major == 0`、`unresolved <= 3`。
- **Oracle 上限**：即使清空 candidate flaws、unresolved_questions 和 conflicts，仅保留 strong support 门槛，也只能恢复 2/9 accept，同时误翻 5 个 reject，说明问题不只是 hygiene cleanup，而是 evidence extraction / unresolved lifecycle / flaw lifecycle / decision interface 四者共同锁死。
- **阶段 2 不应直接进入 runtime 修复**：Claim-Evidence Reconciliation + Stale Gap Cleanup 仍值得做 state hygiene，但不能期待它单独恢复 accept recall。下一步应先做 4B 快速实验验证 evidence extraction 与 unresolved/flaw lifecycle 是否能改善 strong support 和 unresolved 分布。

## 5. 产物

- `FULLTEST_HYGIENE_SIMULATION_RESULTS.json`
- `FULLTEST_HYGIENE_SIMULATION_CASE_TABLE.md`
- `scripts/simulate_state_hygiene_decision.py`
