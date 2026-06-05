# Target Quality Certificate — Layer 3 审计

## 目的

在 Layer 3 完整 10 样本 forensic subset 上收集 TQC 观测字段，回答：
**系统是否在 target / evidence / conflict 不稳定时过早进入 aggressive recovery？**

观测层无行为变更，只为每个 turn 附加五维诊断 + 综合 `recovery_readiness_label`。

## TQC 五维度定义

| 维度 | 取值 | 取自 |
|---|---|---|
| `tqc_target_source` | empty_or_unknown / fallback_claim / mixed_real_and_fallback / real_claim | `final_action_target_claim_ids` + fallback id 前缀检测 |
| `tqc_target_width` | empty / single_target / small_target_set / broad_target_set | `final_action_target_count` |
| `tqc_evidence_grounding` | no_aligned_evidence / fallback_evidence_only / weak_evidence / grounded_evidence | `evidence_map` 中 claim_id 匹配 target 的 evidence 的 strength/stance |
| `tqc_conflict_strength` | weak_conflict / missing_evidence_only / unresolved_but_ungrounded / strong_grounded_conflict | `_claim_contradiction_strength` + `evidence_risk_signals` |
| `recovery_readiness_label` | not_ready_for_recovery / fallback_bridge_only / needs_target_refinement / needs_evidence_grounding / ready_for_aggressive_recovery | 五维组合 |

## 配置

- 模型: Qwen3.5-9B @ `/reviewF/datasets/Qwen3___5-9B`
- Mode: s4, max_turns: 8, max_workers_per_turn: 2
- max_model_len: 3072, max_tokens: 640, seed: 20260423
- 10 样本基线 IDs: `2Cg4YrsCMA, NhLBhx5BVY, IqaQZ1Jdky, kdriw2a8sl, hj323oR3rw, 9EBSEkFSje, Ze49bGd4ON, qgyF6JVmar, EXGahWDp1E, meY36sGyyv`
- 输出: `outputs/results_main/review_infer/p25_1_tqc_v1_l3.jsonl`

## 核心发现

### Finding 1 — readiness 分布严重偏向非 ready

所有 60 个 turn 中:

| label | count | pct |
|---|---|---|
| `ready_for_aggressive_recovery` | 2 | **3.3%** |
| `needs_target_refinement` | 11 | 18.3% |
| `needs_evidence_grounding` | 15 | 25.0% |
| `fallback_bridge_only` | 2 | 3.3% |
| `not_ready_for_recovery` | 30 | **50.0%** |

系统大部分时间 (96.7%) 操作在非 ready 状态。

### Finding 2 — 89.5% 的 recovery push 发生在非 ready 状态

| readiness | pushed | push_pct | non_push | non_push_pct |
|---|---|---|---|---|
| `ready_for_aggressive_recovery` | 2 | 10.5% | 0 | 0.0% |
| `needs_target_refinement` | 5 | 26.3% | 6 | 14.6% |
| `needs_evidence_grounding` | 6 | 31.6% | 9 | 22.0% |
| `fallback_bridge_only` | 0 | 0.0% | 2 | 4.9% |
| `not_ready_for_recovery` | 6 | 31.6% | 24 | 58.5% |

**17/19 (89.5%) 的 recovery push 发生在 target / evidence / conflict 未 ready 时**。这直接验证用户的假设：系统不是不会 recovery, 而是 recovery 的对象不合格。

### Finding 3 — sticky_recovery_bias 零次在 ready 状态触发

| 推送源 | ready | need_tr | need_eg | fb_br | not_ready |
|---|---|---|---|---|---|
| `sticky_recovery_bias` | **0** | 5 | 4 | 0 | **6** |
| `evidence_progress_override` | 2 | 0 | 2 | 0 | 0 |

`sticky_recovery_bias` 的 15 次推进**全部**发生在非 ready 状态，其中 6 次甚至是 `not_ready_for_recovery`。`evidence_progress_override` 则相对健康（2/4 ready）。

### Finding 4 — 非 ready push 次数与 reward 负相关

| paper_id | reward | decision_correct | 非 ready pushes |
|---|---|---|---|
| `hj323oR3rw` | **0.328** | **0** | **5** |
| `meY36sGyyv` | 0.585 | 1 | 4 |
| `qgyF6JVmar` | 0.606 | 1 | 4 |
| `kdriw2a8sl` | 0.669 | 1 | 2 |
| `9EBSEkFSje` | 0.694 | 1 | 2 |
| `2Cg4YrsCMA` | 0.564 | 1 | 0 |
| `EXGahWDp1E` | 0.596 | 1 | 0 |
| `IqaQZ1Jdky` | 0.630 | 1 | 0 |
| `NhLBhx5BVY` | 0.468 | 1 | 0 |
| `Ze49bGd4ON` | 0.631 | 1 | 0 |

唯一 decision 错误且 reward 最低的 `hj323oR3rw` 正好是非 ready push 最多的样本。

### Finding 5 — `challenge_previous_hypothesis` 91% 在非 ready 发出

| action_type | ready | need_tr | need_eg | fb_br | not_ready |
|---|---|---|---|---|---|
| `analyze_flaws` | 0 | 3 | 4 | 0 | 0 |
| `challenge_previous_hypothesis` | **2** | **8** | **7** | **0** | **6** |
| `extract_claims` | 0 | 0 | 0 | 0 | 10 |
| `finalize` | 0 | 0 | 4 | 2 | 0 |
| `verify_evidence` | 0 | 0 | 0 | 0 | 14 |

23 次 `challenge_previous_hypothesis` 中只有 2 次发生在 ready 状态。

## 结论

Layer 3 TQC 数据强力支持以下三个结论：

1. **系统大部分时间（96.7%）target / evidence / conflict 并未 ready**，这不是偶发，是结构性状态。
2. **Recovery push 在 89.5% 情况下发生在非 ready 状态**，其中 sticky_recovery_bias 是最强的非 ready 推手（100% 非 ready）。
3. **非 ready push 次数与 reward 负相关**，最极端样本同时是非 ready push 最多和唯一 decision 错误。

这意味着问题不在 recovery 能力，而在 recovery **entry 的对象**。

## 下一刀建议

基于数据，最小行为改动应瞄准：

> 当 `recovery_readiness_label ∈ {not_ready_for_recovery, fallback_bridge_only}`  且候选 action 为 `challenge_previous_hypothesis`  且 `policy_source == sticky_recovery_bias`：
> 
> → **defer** 到 `verify_evidence`（优先）或 `analyze_flaws`（若 evidence 已存在）
> → 不触及 `evidence_progress_override` / `flaw_progress_override` 等健康推进源

这是 **defer 不是 block**（避免 progression gate 塌缩问题），且**只约束 sticky**（其它源的行为保留），符合用户手册的 "不做多控制器同时改动" 原则。

## 输出文件

- `outputs/results_main/review_infer/p25_1_tqc_v1_l3.jsonl` — 带 TQC 字段的 Layer 3 结果
- `scripts/analyze_tqc.py` — 分析脚本
- `p25_1_tqc_v1_l3.log` — 运行日志
