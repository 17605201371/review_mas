# p25.1 flaw_fix_v2 实验汇总

## 改动说明

本次包含三项修复，从 p25.1 mainline baseline 出发，不改变 controller 逻辑，只修 bug 和度量问题。

### 修复 1：flaw_progress_override 解除阻塞（review_manager_policy.py）

- **问题**：3/10 样本（2Cg4YrsCMA, kdriw2a8sl, EXGahWDp1E）卡在 `verify_evidence` 循环 6–7 轮，从不进入 `analyze_flaws`
- **根因**：`evidence_progress_override` 将 `policy_source` 从 `"manager_model"` 改为 `"evidence_progress_override"`；下游 `flaw_progress_override` 要求 `policy_source == "manager_model"` 永远不触发
- **修复**：新增 `_flaw_eligible_sources = {"manager_model", "evidence_progress_override", "s4_clarification_to_evidence_override"}`，允许上游 override 也触发 flaw progression

### 修复 2：structured report 安全网（state.py render_final_review）

- **问题**：当模型显式生成 `final_report` 时，函数直接返回，报告可能缺少 strengths/weaknesses/suggestions section
- **修复**：始终走 5-section 结构化模板，模型报告内容注入 summary section

### 修复 3：section 检测修复（reward.py _extract_sections）

- **问题 A**：`_try_parse_json_text` → `_normalize_text` 将所有换行压成空格，整个报告变成一行，行级 section header 检测失败（section_presence 永远 = 0.4）
- **问题 B**：`"5. Reason for Decision"` 被 decision pattern 错误匹配，覆盖真正的 decision 内容
- **修复 A**：对含换行的非 JSON 文本保留原始换行
- **修复 B**：`lower.startswith("reason for")` 时跳过 section pattern 匹配

## 配置对齐

| 参数 | 基线 | 候选 | 备注 |
|---|---|---|---|
| mode | s4 | s4 | ✓ |
| model | Qwen3.5-9B | Qwen3.5-9B | ✓ |
| max_turns | 8 | 8 | ✓ |
| max_workers_per_turn | 2 | 2 | ✓ |
| max_model_len | 3072 | 3072 | ✓ |
| max_tokens | 640 | 640 | ✓ |
| temperature | 0.2 | 0.2 | ✓ |
| top_p | 0.95 | 0.95 | ✓ |
| seed | 20260423 | 20260423 | ✓ |
| max_num_seqs | 128 | 16 | RTX 4090 Mamba 限制 |
| gpu_memory_utilization | 0.94 | 0.85 | RTX 4090 显存限制 |
| enforce_eager | false | true | CUDA graph 不影响输出 |

max_num_seqs / gpu_memory_utilization / enforce_eager 影响 batching 和 CUDA graph，不影响单样本生成结果（temperature/top_p/seed 一致）。

## Layer 3 结果（10 样本完整 forensic subset）

| paper_id | 基线(old) | 基线(sec_fix) | 候选(raw) | 候选(sec_fix) | delta | 方向 |
|---|---|---|---|---|---|---|
| 2Cg4YrsCMA | 0.5384 | 0.5864 | 0.4904 | 0.5384 | -0.0480 | ↓ |
| 9EBSEkFSje | 0.6410 | 0.6890 | 0.7300 | 0.7780 | +0.0890 | ↑ |
| EXGahWDp1E | 0.6499 | 0.6979 | 0.7257 | 0.7737 | +0.0757 | ↑ |
| IqaQZ1Jdky | 0.5825 | 0.6305 | 0.5588 | 0.6068 | -0.0237 | ↓ |
| NhLBhx5BVY | 0.5374 | 0.5854 | 0.5919 | 0.6399 | +0.0544 | ↑ |
| Ze49bGd4ON | 0.4661 | 0.5141 | 0.5701 | 0.6181 | +0.1040 | ↑ |
| hj323oR3rw | 0.2472 | 0.2952 | 0.3452 | 0.3932 | +0.0980 | ↑ |
| kdriw2a8sl | 0.6439 | 0.6919 | 0.6396 | 0.6876 | -0.0042 | ≈ |
| meY36sGyyv | 0.5431 | 0.5911 | 0.5985 | 0.6465 | +0.0554 | ↑ |
| qgyF6JVmar | 0.5935 | 0.6415 | 0.6095 | 0.6575 | +0.0160 | ↑ |
| **MEAN** | **0.5443** | **0.5923** | **0.5860** | **0.6340** | **+0.0417** | |

- **Decision correct**: 9/10 → 9/10（持平）
- **Win/Tie/Loss**: 7 / 1 / 2
- **Net improvement**: +0.0417（公平 section 修复对比下的净行为改进）

## 实验漏斗遵循情况

- Layer 1（2 条冒烟集）：2Cg4YrsCMA, kdriw2a8sl → 打破 stall 确认 ✓
- Layer 2（5 条功能集）：+5 条 → net +0.0135 ✓
- Layer 3（10 条完整集）：全量 → net +0.0417 ✓

## 输出文件

- `outputs/results_main/review_infer/p25_1_flaw_fix_v2_l3.jsonl` — Layer 3 完整结果
- `outputs/results_main/review_infer/p25_1_flaw_fix_v2_l2.jsonl` — Layer 2 结果
- `outputs/results_main/review_infer/p25_1_flaw_fix_v2_l1.jsonl` — Layer 1 结果
- `p25_1_flaw_fix_v2_l3.log` — Layer 3 运行日志
