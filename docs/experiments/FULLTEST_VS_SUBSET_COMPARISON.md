# 39-Sample 完整测试集 vs 10-Sample Forensic Subset 对比

**日期**：2026-04-24
**动机**：验证 10-sample forensic subset 上"mainline 0.6251 + 9/10 decision correct"的数字是否反映真实能力，还是 subset 偏态造成的假象。
**答案**：**subset 数字是假象。** 真实分布下系统完全不 accept，decision_correct 等于 always-reject baseline。

---

## 0. 配置对齐

| 项 | 值 |
|---|---|
| 模型 | Qwen3.5-9B @ `/reviewF/datasets/Qwen3___5-9B` |
| mode | s4 |
| max_turns | 8 |
| max_workers_per_turn | 2 |
| manager_batch_size | 1 |
| max_model_len / max_tokens | 3072 / 640 |
| temperature / top_p | 0.2 / 0.95 |
| seed | 20260423 |
| max_num_seqs | 16 |
| gpu_memory_utilization | 0.85 |

**完全同配置**，唯一差异是数据集（10-sample subset vs 39-sample full test）。

---

## 1. 核心对比表（Table 1）

| 配置 | n | reward mean | min | max | decision_correct | always-reject baseline | accept recall | pred_dist |
|---|---|---|---|---|---|---|---|---|
| flaw_fix_v2 (10-subset) | 10 | **0.5860** | 0.3452 | 0.7300 | **9/10 = 90.0%** | 0/10 = 0.0%\* | 0/1 | `{reject: 10}` |
| tqc_v1 (10-subset)      | 10 | **0.5771** | 0.3275 | 0.6940 | **9/10 = 90.0%** | 0/10 = 0.0%\* | 0/1 | `{reject: 10}` |
| **fulltest (39-full)**  | 39 | **0.4702** | 0.1128 | 0.6827 | **30/39 = 76.9%** | **30/39 = 76.9%** | **0/9** | `{reject: 39}` |

\* 10-subset 的 "always-reject baseline 0%" 是分子分母同一口径的错误展示；实际含义是 9 reject + 1 accept 的子集，always-reject 会得 9/10=90%，与系统一致。

**关键观察**：
- **系统 decision acc 完全等于 always-reject baseline**（39/39 个预测都是 `reject`，accept recall = 0/9）
- Subset 上的 90% 看起来是"系统能力"，实则因为 subset 是 9 reject + 1 accept（90% reject），**系统"什么都不干"也能拿到 9/10**
- full test 上的 76.9% 同样等于 always-reject；subset 与 full 的一致性证明 **系统在 accept 上 100% 失败**

---

## 2. Reward 分量对比（Table 2）

| 分量 | ff2 (10) | tqc (10) | full (39) | delta full - tqc |
|---|---|---|---|---|
| `decision` | 0.9000 | 0.9000 | **0.7692** | **-0.1308** |
| `rating_align` | 0.0000 | 0.0000 | 0.0000 | +0.0000 |
| `decision_line_bonus` | 0.0800 | 0.0800 | 0.0800 | +0.0000 |
| `section_presence` | 0.4000 | 0.4000 | 0.4000 | +0.0000 |
| `summary_align` | 0.4798 | 0.4434 | 0.4011 | **-0.0422** |
| `strength_align` | 0.4792 | 0.4430 | 0.4010 | **-0.0420** |
| `weakness_align` | 0.4792 | 0.4430 | 0.4010 | **-0.0420** |
| `suggestion_align` | 0.4792 | 0.4430 | 0.4010 | **-0.0420** |
| `global_align` | 0.4792 | 0.4430 | 0.4010 | **-0.0420** |
| `critique` | 0.8500 | 0.8125 | 0.8141 | +0.0016 |
| `stance_align` | 0.5625 | 0.6407 | **0.4825** | **-0.1582** |
| `penalty` | 0.0320 | 0.0320 | **0.0636** | **+0.0316**（越大越差） |
| **`total`** | **0.5860** | **0.5771** | **0.4702** | **-0.1069** |

**解读**：
- `decision` 下降 0.13 = 完全由 9 个 accept 样本被预测成 reject 贡献（0.9 × (1-9/39) = 0.69，跟实际 0.77 差距因为 rounding；实际每个 reject 样本 decision=1.0，9 个 accept 样本 decision=0.0，平均 (30·1 + 9·0)/39 = 0.769 ✓）
- `stance_align` 下降 0.16 —— 第二大降幅。说明 full test 的 paper-side stance 更难对齐
- align 系列（summary/strength/weakness/suggestion/global）**统一下降约 0.04** —— final_report 的文本结构对齐质量整体下滑，但降幅一致说明不是某一节单独问题
- `penalty` 翻倍（0.032 → 0.064）—— 说明 full test 上 penalty triggers 更频繁
- `rating_align = 0.0 across all runs` —— **所有样本都拿 0！** 要么 rating 解析永远失败，要么系统从不输出 rating。此项对 reward 没实质贡献。
- `section_presence / decision_line_bonus` 是常数 —— 结构性分项，与 final_report 的 5-section 格式对齐机制有关（已修）

---

## 3. 按 gold decision 拆分（Table 3）

| gold | n | reward mean | decision | rating_align | stance_align | critique | weakness_align |
|---|---|---|---|---|---|---|---|
| accept | 9 | **0.2244** | **0.0000** | 0.0000 | **0.5427** | 0.7778 | 0.3667 |
| reject | 30 | **0.5439** | **1.0000** | 0.0000 | 0.4644 | 0.8250 | 0.4113 |

**关键观察**：
- accept 样本 reward 只有 reject 样本的 **41%**
- accept 样本 decision **全部归零**（系统从不输出 accept）
- **stance_align 在 accept 样本上反而更高**（0.54 vs 0.46）—— 说明系统对 paper claims 的 stance 判断并没错，只是 final decision 机械规则压制了这个信号
- critique 分数在 accept 上 0.78，在 reject 上 0.83 —— critique generation 本身质量接近
- weakness_align 在 accept 上更低（0.37 vs 0.41）—— 合理：accept 论文应该少 weaknesses，系统却硬塞了 weaknesses，导致对齐差

**潜在破口**：stance_align 在 accept 上 0.54 > reject 上 0.46 提示系统其实"理解" stance 信号，但没让这个信号进入 final_decision。这是 Bug C 的进一步证据。

---

## 4. 混淆矩阵（Table 4）

| | pred=accept | pred=reject |
|---|---|---|
| gold=accept | **0** | **9** |
| gold=reject | **0** | **30** |

精度/召回：
- Accept recall: **0 / 9 = 0%**
- Accept precision: 未定义（分母 0）
- Reject recall: 30 / 30 = 100%
- Reject precision: 30 / 39 = 76.9%

**系统彻底丧失 accept 能力**。39 个样本里没有一次输出 accept。

---

## 5. Bug B 修复模拟（Table 5）

提案："只计算 `status==confirmed` 的 flaws，`candidate` 不计入 reject 阈值"

| 规则 | 正确数 | 准确率 |
|---|---|---|
| 当前规则 | 30/39 | 76.9% |
| 提案规则 | 28/39 | **71.8%**（↓） |
| Delta | **-2** | -5.1pp |

**翻转明细**（reject → accept）：

| paper_id | gold | 效果 |
|---|---|---|
| **hj323oR3rw** | accept | **+1 正确** ✓ |
| NnExMNiTHw | reject | -1 错误 ✗ |
| TPAj63ax4Y | reject | -1 错误 ✗ |
| kam84eEmub | reject | -1 错误 ✗ |

**净结果：+1 - 3 = -2**。Bug B 修复不能单独解决问题。状态特征不足以区分"应 accept"和"候选 flaw 较多的 reject"。

---

## 6. TQC readiness 分布（Table 6）

| readiness | turns | % | push | %push |
|---|---|---|---|---|
| ready_for_aggressive_recovery | 3 | 1.1% | 2 | 1.7% |
| needs_target_refinement | 37 | 13.2% | 13 | 10.9% |
| needs_evidence_grounding | 89 | 31.8% | **54** | **45.4%** |
| fallback_bridge_only | 2 | 0.7% | 0 | 0.0% |
| **not_ready_for_recovery** | **149** | **53.2%** | **50** | **42.0%** |
| **TOTAL** | **280** | | **119** | |

**关键观察**：
- 53.2% 的 turn 处于 `not_ready_for_recovery` 状态
- 但 42.0% 的 `recovery_push_triggered` 也发生在 not_ready 状态下 —— **push 与 ready 状态严重脱钩**
- 45.4% 的 push 发生在 `needs_evidence_grounding`（有目标但证据尚未 grounded）
- 真正 `ready_for_aggressive_recovery` 的 turn 仅占 1.1%，push 中也只占 1.7%
- 与 subset 层级结果一致，TQC 观察层完整暴露了**"系统在 ready 信号未建立时就大量触发 recovery"**的主线病理

这是 Recovery Entry Decision v1 所要解决的问题，但之前的 defer 实验证明**仅 defer 不 push 不能改进 reward**（见 `RECOVERY_ENTRY_DECISION_V1_RESULT.md`）。

---

## 7. 逐样本表（Table 7 - full 39）

按 reward 升序（只显示 decision、rating、stance 三个关键分量）：

| paper_id | gold | pred | reward | dec_c | rating | stance |
|---|---|---|---|---|---|---|
| gzqrANCF4g | Accept | reject | **0.1128** | 0.0 | 0.0000 | 0.2941 |
| 1HCN4pjTb4 | Accept | reject | 0.1704 | 0.0 | 0.0000 | 0.4000 |
| X41c4uB4k0 | Accept | reject | 0.2002 | 0.0 | 0.0000 | 0.3381 |
| LebzzClHYw | Accept | reject | 0.2003 | 0.0 | 0.0000 | 0.4286 |
| jVEoydFOl9 | Accept | reject | 0.2164 | 0.0 | 0.0000 | 0.6000 |
| KI9NqjLVDT | Accept | reject | 0.2472 | 0.0 | 0.0000 | 0.6381 |
| QAAsnSRwgu | Accept | reject | 0.2523 | 0.0 | 0.0000 | 0.6286 |
| BXY6fe7q31 | Accept | reject | 0.2929 | 0.0 | 0.0000 | **0.9455** |
| hj323oR3rw | Accept | reject | 0.3275 | 0.0 | 0.0000 | 0.6111 |
| XyB4VvF01X | Reject | reject | 0.3766 | 1.0 | 0.0000 | 0.4118 |
| ... (reject samples) ... | | | | | | |
| kam84eEmub | Reject | reject | **0.6827** | 1.0 | 0.0000 | 0.5330 |

**最低 9 名全是 accept 样本**。reject 样本 reward 均 ≥ 0.38，accept 样本 reward 均 ≤ 0.33，**完全不重叠**。

特别注意 `BXY6fe7q31`：gold=accept，pred=reject，但 **stance_align = 0.9455**（全 test 最高之一！）。系统对它的 stance 判断极准确，却照样判 reject。这是 **decision logic 与 stance signal 脱钩** 的确凿证据。

---

## 8. 与 subset "mainline 胜出"实验的回溯对比

历史实验记录：

| 实验 | Subset n | Subset reward | Subset dec_correct | 真实 full test 是否跑过 |
|---|---|---|---|---|
| baseline (p25.1 explicit recovery phase) | 10 | ~0.58 | 9/10 | 未跑 |
| flaw_fix_v2 | 10 | **0.6251** | 9/10 | 未跑 |
| TQC v1 observability | 10 | 0.5771 | 9/10 | 未跑 |
| Recovery Entry Decision v1 (rolled back) | 10 | ~0.55 | 8/10 | 未跑 |
| progression_gate_v1 (rolled back) | 10 | 0.48 | 7/10 | 未跑 |
| **当前 mainline (full test)** | **39** | **0.4702** | **30/39** | **本次** |

**发现**：
- 所有历史 "mainline 0.58-0.63" 数字都是 subset 偏态
- 任何两个实验在 subset 上的差别（如 0.58 vs 0.63）都在 0.05 量级，而 subset → full 的 gap 是 0.12 —— **subset 差异可能根本不 reflect full test 差异**
- 也就是说：**我们过去对 "flaw_fix_v2 > baseline" 的判断缺乏 full test validation**

---

## 9. 核心结论

### 9.1 Subset 数字不可信

10-sample subset 上的 90% decision accuracy 与 0.58-0.63 reward 是**数据偏态**（subset 里 9 reject + 1 accept）。真实分布（30 reject + 9 accept）下系统性能**不如 subset 暗示**：
- reward 从 0.58 降至 0.47 (-19%)
- decision_correct 从 90% 降至 77% (-13pp)
- 系统 **= always-reject baseline**

### 9.2 结构性上限已到

系统在 accept 样本上：
- 100% 预测错误（0/9 recall）
- reward 均值仅 0.22（reject 样本的 41%）
- 但 stance_align 反而更高（0.54 vs 0.46）

`stance` 信号是对的，但被 `infer_final_decision` 的机械阈值规则完全压制（Bug C）。

### 9.3 Bug B 修复方向无效

在 full test 上模拟"confirmed-only flaws"规则：
- hj323oR3rw 翻转成功 (+1)
- NnExMNiTHw / TPAj63ax4Y / kam84eEmub 被误翻 (-3)
- 净效果 **-2**

**现有 state 特征不足以线性分离 accept / reject**。

### 9.4 TQC 观察确认主线病理

- 53% turn 处于 not_ready
- 42% push 发生在 not_ready
- **"系统在证据未建立时过早进入 recovery"** 的假设被完整验证

但主线实验表明 defer 这些 push 不能提升 reward（见 Recovery Entry Decision v1 失败记录）——说明**问题不只是过早 push，而是整个 recovery 管线设计**。

---

## 10. 建议的下一步

三条候选路径，按 ROI 降序：

### 路径 A：停手写论文（推荐）

将本文档 + `HJ323_CASEBOOK.md` + Bug A-D + TQC 失败实验，打包成结构性诊断论文。

**卖点**：
1. 10-sample forensic subset 过度乐观的陷阱（Bug D）—— 其他论文很少披露
2. decision logic 与 stance signal 脱钩（Bug C 的 `BXY6fe7q31` 案例是金子）
3. Recovery-Failure Echo Into Critique Weakness（Bug A）—— 具体 pipeline 伪迹
4. `candidate` flaw 与 `confirmed` flaw 同权导致误判（Bug B）
5. 状态特征不可分离的 `hj323oR3rw vs meY36sGyyv` 反例

**风险**：零。数字就是数字。

### 路径 B：改 manager prompt 让 LLM 显式输出 final_decision

绕开 `infer_final_decision` 机械规则，让 manager 在最后一轮读自己的 state 给判断。

**卖点**：可能把 stance_align 的高分转化成 decision 上的 accept。
**风险**：LLM 同样可能倾向 reject；需要 9B 完整 test ≈ 2-3h 验证。

### 路径 C：在 4B 上快速 prompt 探索，再上 9B

**卖点**：4B 上迭代 15-30 min 就能看到 accept 覆盖率是否提升。
**风险**：4B 的 prompt 行为不一定平移到 9B；可能探索方向是 4B-specific。

---

## 11. 附录：Commit 与产物

- **本次 full test 跑出物**：`outputs/results_main/review_infer/p25_1_fulltest_mainline.jsonl` (39 rows)
- **对比脚本**：`scripts/compare_mainline_fulltest.py`
- **10-sample subset 对比基线**：
  - `outputs/results_main/review_infer/p25_1_flaw_fix_v2_l3.jsonl`
  - `outputs/results_main/review_infer/p25_1_tqc_v1_l3.jsonl`
- **关联文档**：
  - `docs/experiments/HJ323_CASEBOOK.md`
  - `docs/experiments/EXPERIMENT_LOG.md`
  - `docs/experiments/FAILED_EXPERIMENTS.md`
  - `docs/experiments/POSITIVE_EXPERIMENTS.md`
