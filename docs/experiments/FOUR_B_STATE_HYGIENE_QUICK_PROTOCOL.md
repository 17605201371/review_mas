# 4B State Hygiene Quick Experiment Protocol

**日期**：2026-04-25
**目的**：在不继续堆 controller 的前提下，用 4B 快速验证 state hygiene 相关入口是否能改善 `strong_support`、`unresolved`、candidate flaw 生命周期和 final decision interface。

---

## 1. 为什么不是直接改 runtime

阶段 1 offline simulation 已证明：

- Claim-Evidence Reconciliation：0 翻转
- Stale Gap Cleanup：0 翻转
- Meta / Excerpt Flaw Filtering：0 翻转
- Candidate flaw 降权：0 翻转
- 组合规则：0 翻转

原因是当前 `infer_final_decision` 不直接读取 `claim.status` 或 `evidence_gaps`，而是被以下硬条件共同锁死：

| blocker | samples |
|---|---:|
| `strong_support < 2` | 28/39 |
| `unresolved >= 6` | 18/39 |
| `critical >= 1` | 14/39 |
| `major >= 2` | 6/39 |
| `conflicts >= 4` | 1/39 |

因此，下一步不是直接实现 Claim-Evidence Reconciliation + Stale Gap Cleanup 并期待 decision 变好，而是先用 4B 快速实验回答：**到底哪个入口能真正改变这些 blocker 分布**。

---

## 2. 本轮 4B 快速实验要验证的四个问题

### Q1: Evidence extraction 是否能提高 `strong_support >= 2` 覆盖

当前很多 accept 样本甚至没有足够 `strong_support`，导致 oracle 清空 flaws/unresolved 后仍无法 accept。

观察指标：

- `strong_support_count`
- `gold_accept_strong_support_ge2_count`
- `unsupported_with_strong_support_count`
- `unsupported_with_2plus_strong_count`

### Q2: Unresolved lifecycle 是否能减少 `unresolved >= 6`

当前 open unresolved 堆积是第二大 reject blocker。

观察指标：

- `unresolved_count`
- `unresolved_ge6_count`
- `generic_unresolved_count`
- `resolved_unresolved_count`
- `stale_evidence_gap_count`

### Q3: Flaw lifecycle 是否能降低 candidate critical/major 硬锁

当前 candidate critical / major 会直接触发 reject，但 confirmed 极少。

观察指标：

- `candidate_critical_count`
- `candidate_major_count`
- `confirmed_flaw_count`
- `downgraded_flaw_count`
- `retracted_flaw_count`
- `candidate_major_used_for_reject_count`

### Q4: Decision interface 是否应显式读取 hygiene/confidence 信号

如果 4B 改了 evidence/unresolved/flaw 分布，但 final decision 仍 always-reject，说明问题在 decision interface。

观察指标：

- predicted accept count
- accept recall
- reject recall
- macro-F1
- always-reject gain
- blocker distribution before/after

---

## 3. 样本选择

本轮使用 16 条 4B focus subset。

### 3.1 全部 gold accept 样本（9 条）

这些是恢复 accept recall 的核心：

- `hj323oR3rw`
- `QAAsnSRwgu`
- `X41c4uB4k0`
- `gzqrANCF4g`
- `KI9NqjLVDT`
- `1HCN4pjTb4`
- `LebzzClHYw`
- `BXY6fe7q31`
- `jVEoydFOl9`

### 3.2 Oracle false-accept reject 对照（5 条）

这些样本在 oracle 清空 candidate/unresolved 后会被误翻 accept，是防止过度放宽规则的关键对照：

- `NnExMNiTHw`
- `fGXyvmWpw6`
- `TPAj63ax4Y`
- `aTBE70xiFw`
- `kam84eEmub`

### 3.3 稳定 reject controls（2 条）

用于检测系统是否整体偏 accept 或过度清理：

- `GE6iywJtsV`
- `KOUAayk5Kx`

---

## 4. 4B 运行配置

### 行为对齐优先配置（推荐第一轮）

尽量保持与 9B full-test 行为配置一致，只替换模型路径和并发参数：

```bash
python -u -m agent_system.inference.review_runner \
  --dataset-path outputs/subsets/state_hygiene_4b_focus.parquet \
  --model-path /reviewF/datasets/Qwen3___5-4B \
  --temperature 0.2 \
  --top-p 0.95 \
  --mode s4 \
  --max-turns 8 \
  --max-workers-per-turn 2 \
  --manager-batch-size 1 \
  --gpu-memory-utilization 0.60 \
  --max-num-seqs 64 \
  --max-model-len 3072 \
  --max-tokens 640 \
  --output-path outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl
```

### 吞吐优先配置（第二轮可选）

参考历史 4B recovery regression：

- `max_turns=15`
- `max_workers_per_turn=3`
- `manager_batch_size=1 or 2`
- `gpu_memory_utilization=0.55~0.60`
- `max_num_seqs=64~128`

---

## 5. 判定标准

本轮 4B 快速实验不是为了刷 accuracy，而是验证 blocker 是否被改善。

### 必须改善

至少满足一项：

1. gold accept 中 `strong_support >= 2` 覆盖增加
2. `unresolved >= 6` 样本数下降
3. candidate critical / candidate major 计数下降
4. confirmed / downgraded / retracted flaw 生命周期开始出现
5. predicted accept count > 0 且 false accept 不爆炸

### 不能接受

- accept recall 仍为 0，且 blocker 分布没有改善
- reject controls 大量被误翻 accept
- grounded weakness rate 下降
- meta weakness 增加
- recovery commit 后 state 更不一致

---

## 6. 本轮不做什么

- 不改 sticky
- 不改 throttle / progression gate / recovery entry defer
- 不改 final decision threshold
- 不全局压制 fallback
- 不同时改 runtime 多个 controller

---

## 7. 输出文件

建议输出：

- `outputs/subsets/state_hygiene_4b_focus.parquet`
- `outputs/subsets/state_hygiene_4b_focus_meta.json`
- `outputs/results_main/review_infer/p25_1_state_hygiene_4b_focus.jsonl`
- `docs/experiments/FOUR_B_STATE_HYGIENE_QUICK_RESULT.md`

评估时复用：

- `scripts/audit_fulltest_hygiene.py` 的指标框架
- `scripts/simulate_state_hygiene_decision.py` 的 blocker 诊断逻辑

---

## 8. 下一步决策

如果 4B 能改善 blocker 分布，再决定是否进入 runtime 修复：

1. 若 `strong_support` 改善明显：优先修 evidence extraction / support grading
2. 若 `unresolved` 改善明显：优先做 unresolved lifecycle cleanup
3. 若 flaw lifecycle 改善明显：单独开 Flaw Provenance & Confirmation v1
4. 若以上改善但 decision 仍 reject：改 decision interface，让它读 hygiene/confidence 信号
5. 若全部无改善：说明问题不是单个 hygiene patch，而是 prompt/schema 设计层问题
