# Project Structure — Dr. MAS for Paper Review

Dr. MAS 多智能体系统在 DeepReview-13K 上做 S4 模式论文评审的仓库架构说明。
最近一次更新：2026-04-24（TQC observability + 文档重整 + RED v1 回滚）。

---

## 当前主线

`p25.1 baseline + explicit recovery phase + flaw_fix_v2 (+0.0417) + TQC observability v1`

- **分支**: `codex/p25-1-explicit-mainline`
- **Layer 3 10 样本 mean reward**: 0.6251
- **Decision correct**: 9/10
- 详见 [`EXPERIMENT_LOG.md`](EXPERIMENT_LOG.md) 和 [`docs/experiments/`](docs/experiments/)

---

## 根目录

### 项目级文档（10 个 .md）

| 文件 | 作用 |
|---|---|
| `README.md` | 项目概述和快速开始 |
| `AGENT.md` | 开发/代理操作指南（给 Cascade / 未来 maintainer） |
| `TASK.md` | 任务描述（S4 multi-turn review） |
| `TASK_WALKTHROUGH.md` | 任务流程走查 |
| `MAINLINE_BASELINE.md` | 主线基线记录 |
| `COMPLETED_TASKS_SUMMARY.md` | 已完成任务总结 |
| `NEXT_MODEL_HANDOFF_PLAN_2026-04-15.md` | 模型交接计划 |
| `PROJECT_STRUCTURE.md` | 本文件 |
| `EXPERIMENT_LOG.md` | 实验索引（指向 `docs/experiments/`） |
| `memory.md` | 长期记忆 / 决策笔记 |

### 顶层目录

| 目录 | 作用 |
|---|---|
| `agent_system/` | 多智能体核心逻辑（环境、策略、prompts、推理） |
| `docs/experiments/` | 实验文档（成功/失败汇总 + 原始归档） |
| `logs/` | 所有 Layer 1/2/3 运行日志（`.log`） |
| `outputs/` | 推理 & 评估结果（`*.jsonl`，大量） |
| `scripts/` | 30 个工具脚本（推理、分析、对比） |
| `tests/` | pytest 单元测试 |
| `examples/` | 训练 & 数据处理脚本 |
| `recipe/` | 训练配置 |
| `src/` | 部分 RL 源码 |
| `verl/` | 底层 RL 框架（VERL） |
| `docker/` | 容器化配置 |
| `completed_task_docs/` | 历史任务产出 |

---

## `agent_system/` — 核心代码

```
agent_system/
├── review_manager_policy.py       # Manager policy + TQC observability
├── review_prompts.py              # Review 相关 prompt 模板
├── agent/                         # Agent / orchestration 定义
│   ├── agents/review/             # Reviewer / Meta-Reviewer
│   └── orchestra/review/          # 多轮调度
├── environments/
│   ├── env_manager.py             # Env lifecycle
│   └── env_package/review/        # Review 环境核心
│       ├── envs.py                # Env wrapper
│       ├── state.py               # State / turn_log schema (含 TQC 字段)
│       ├── reward.py              # Reward 计算 (含 section_presence 修复)
│       ├── recovery_patch.py      # Recovery patch 解析
│       └── recovery_validator.py  # Recovery 验证
├── inference/
│   └── review_runner.py           # 推理入口
├── multi_turn_rollout/            # 多轮 rollout 工具
├── memory/                        # Agent memory
└── reward_manager/                # Reward 管理器
```

### 关键文件 — 最近改动

| 文件 | 改动 | 对应 commit |
|---|---|---|
| `review_manager_policy.py` | flaw_progress_override / structured report / TQC 5 维 / RED v1 defer 行为（已回滚） | `8c19466`, `84a968c`, `e1f8f1e` |
| `environments/env_package/review/state.py` | TQC 字段 normalize + turn_log 传播 / recovery_entry_deferred 字段 | `84a968c`, `fbb7364` |
| `environments/env_package/review/reward.py` | section detection 健壮化 | `8c19466` |

---

## `docs/experiments/` — 实验文档

三份汇总（从散落在根目录的 31 个实验文档整理而来）：

```
docs/experiments/
├── EXPERIMENT_LOG.md              # 时间线索引
├── POSITIVE_EXPERIMENTS.md        # 成功改动 (flaw_fix_v2, TQC obs)
├── FAILED_EXPERIMENTS.md          # 失败改动 + Do Not Retry 列表 + 共同教训
└── archive/
    ├── p25_0/                     # 7 文档：基线建立
    ├── p25_1/                     # 11 文档：iteration subset + flaw_fix_v2
    ├── progression_gate_v1/       # 5 文档：❌ progression_gate 失败
    ├── forensic_v2/               # 5 文档：target / recovery push 溯源
    └── tqc_and_red_v1/            # 3 文档：TQC audit + ❌ RED v1 失败
```

---

## `scripts/` — 工具脚本

30 个脚本，主要类别：

| 脚本 | 作用 |
|---|---|
| `run_review_infer.py` | Layer 1/2/3 推理入口（Qwen3.5-9B + vLLM） |
| `analyze_tqc.py` | TQC 5 维 + readiness 分布 / defer 统计分析 |
| `p25_1_analyze.py` | p25.1 系列 pairwise 对比 |
| `p25_0_frozen_compare.py` | p25.0 frozen compare |
| `p24_*_audit.py` / `p24_*_stability.py` | p24 系列 recovery audit / activation 稳定性 |
| `build_pilot_reports.py` | 生成 pilot report |
| `download_deepreview.py` | 下载 DeepReview-13K 数据 |
| `compare_review_modes.py` | 模式对比（S3 vs S4） |
| `install_vllm_sglang_mcore.sh` | 环境安装 |

---

## `tests/` — 单元测试

关键测试：
- `test_review_multiturn.py` — multi-turn review 状态机（6 用例，全绿）
- `test_review_inference_runner.py` — 推理入口测试

运行：`python3 -m pytest tests/test_review_multiturn.py -q`

---

## `logs/` — 运行日志（9 个 .log）

Layer 1/2/3 推理运行日志。本目录在 `.gitignore` 中，但主线关键实验的日志已强制追踪（`git add -f`）以保证可复现性。

---

## `outputs/` — 推理结果

`outputs/results_main/review_infer/*.jsonl` 下存放所有 Layer 1/2/3 推理结果。最近关键结果：

| 文件 | 说明 |
|---|---|
| `p25_1_flaw_fix_v2_l3.jsonl` | flaw_fix_v2 Layer 3（+0.0417）✅ |
| `p25_1_tqc_v1_l3.jsonl` | TQC observability Layer 3（当前主线基线）✅ |
| `p25_1_red_v1_l3.jsonl` | Recovery Entry Decision v1 Layer 3（−0.0105）❌ |

---

## 外部存储（`/reviewF/`）

```
/reviewF/
├── datasets/
│   ├── WestLakeNLP___deep_review-13_k/   # 原始数据（ModelScope）
│   ├── drmas_review/                      # 处理后的 parquet
│   └── Qwen3___5-9B/                      # 推理用基础模型（当前固定）
└── outputs/                              # 训练/实验输出（与本仓库 outputs/ 同步）
```

---

## 工作流

### 运行单次 Layer 3 推理（10 样本 forensic subset）

```bash
conda run -n DrMAS-qwen35 env PYTHONPATH=/root/zssmas_mainline python3 scripts/run_review_infer.py \
  --model-path /reviewF/datasets/Qwen3___5-9B \
  --dataset-path outputs/results_main/review_infer/p25_1_iteration_subset.parquet \
  --mode s4 --max-turns 8 --max-workers-per-turn 2 \
  --max-model-len 3072 --max-tokens 640 \
  --temperature 0.2 --top-p 0.95 \
  --seed 20260423 --enforce-eager \
  --output-path outputs/results_main/review_infer/<实验名>.jsonl \
  > logs/<实验名>.log 2>&1
```

耗时：约 30–40 分钟。

### 分析 TQC 指标

```bash
python3 scripts/analyze_tqc.py outputs/results_main/review_infer/<实验名>.jsonl
```

### 跑测试

```bash
python3 -m pytest tests/test_review_multiturn.py -q
```

---

## 最近关键变更（2026-04-23 ~ 2026-04-24）

| 日期 | Commit | 变更 | 状态 |
|---|---|---|---|
| 04-23 | `8c19466` | flaw_fix_v2：bug 修复批次（flaw_progress_override / structured report / section detection） | ✅ 保留 (+0.0417) |
| 04-24 | `84a968c` | TQC observability v1：5 维诊断 + Layer 3 审计 | ✅ 保留 |
| 04-24 | `fbb7364` | Recovery Entry Decision v1：defer non-ready sticky push | ❌ 测试失败 (−0.0105) |
| 04-24 | `e1f8f1e` | revert: 回滚 RED v1 defer 行为，保留 TQC 字段 | ✅ 当前主线 |
| 04-24 | `12bc875` | docs: 根目录重整（46→10 .md），实验归档至 `docs/experiments/` | ✅ 结构性 |

---

## 下一步方向（见 `docs/experiments/POSITIVE_EXPERIMENTS.md` 末尾）

**Readiness Repair / Target Refinement v1** — 从"阻止 recovery"转向"target 不 ready 时主动建设内容"，按 TQC label 分流做正向干预。

**不要再做**（见 `docs/experiments/FAILED_EXPERIMENTS.md`）：
- progression_gate / throttle / gate 任何变体
- sticky 新版本 / 扩展
- fallback 全局 suppress
- 任何基于"阻断 recovery 的简单规则"
