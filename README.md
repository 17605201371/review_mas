# DrMAS Review

本项目不再把自己描述成“通用多智能体强化学习框架”，而是聚焦为一个面向英文论文评审辅助的多轮对话系统。

当前仓库的核心研究问题是：

- 多轮交互是否能提升自动审稿中的证据对齐与缺陷定位能力。
- 角色分工的多智能体是否能缓解多轮对话中的错误累积。

为此，仓库将原有 Dr.MAS 训练骨架适配为一个专门的 `review` 任务：围绕一篇论文逐轮维护 `ReviewState`，由 manager 决定是否继续分析、调用哪些角色、以及何时收敛到最终审稿意见。

## 一句话

做一个面向英文论文评审辅助的多轮对话系统，研究多轮交互是否能提升证据对齐与缺陷定位，以及角色分工的多智能体是否能缓解多轮对话中的错误累积。

## 当前主线基线

当前仓库已经明确将 `p25.1` 定义为**唯一主线基线**。

主线结论只来自两组冻结实验：

- `p25.0`: 4B vs 9B frozen recovery-quality compare
- `p25.1`: 9B recovery-quality expansion

这条主线回答的问题是：

> 在多轮 review assistance 中，关键不只是触发 recovery，而是让 recovery 以 structured patch 的形式有效改变 `ReviewState`；在这一框架下，9B 相比 4B 主要提升的是 patch effectiveness，而不是总 reward。

后续 `p25.2` 到 `p25.5a` 的实验保留为探索性诊断材料，用于 negative findings、limitations 和 future work，不再并入主结论。主线与探索结果的目录边界见根目录 [MAINLINE_BASELINE.md](MAINLINE_BASELINE.md)。

## 当前任务定义

输入不是一句“帮我审稿”，而是一个包含论文文本、用户目标和参考评审信息的 review episode。

系统每轮都会围绕一份任务私有黑板状态 `ReviewState` 工作，而不是只把整篇论文和全量历史反复拼回 prompt。当前 `ReviewState` 至少包含：

- `claims`
- `evidence_map`
- `flaw_candidates`
- `unresolved_questions`
- `dialogue_summary`
- `turn_id`

另外，当前实现还维护：

- `mode`
- `final_decision`
- `final_report`
- `last_focus`

对应代码在 [agent_system/environments/env_package/review/state.py](agent_system/environments/env_package/review/state.py)。

## 系统结构

当前实现采用 manager 驱动的多轮审稿流程：

1. `ReviewEnv` 在 `reset/step` 中维护任务级 `ReviewState`，并在每轮返回新的 observation。
2. `ReviewMultiAgentOrchestra` 先调用 manager，再按 manager 的路由结果选择 worker agents。
3. 各 worker 以严格 JSON 输出更新各自负责的状态字段。
4. env 合并 manager 与 worker 的结构化输出，记录 turn log，并决定继续还是 finalize。

关键模块：

- 环境与状态：
  - [agent_system/environments/env_package/review/envs.py](agent_system/environments/env_package/review/envs.py)
  - [agent_system/environments/env_package/review/state.py](agent_system/environments/env_package/review/state.py)
  - [agent_system/environments/env_manager.py](agent_system/environments/env_manager.py)
- orchestra：
  - [agent_system/agent/orchestra/review/review_orchestra.py](agent_system/agent/orchestra/review/review_orchestra.py)
- agents：
  - [agent_system/agent/agents/review/manager_agent.py](agent_system/agent/agents/review/manager_agent.py)
  - [agent_system/agent/agents/review/claim_agent.py](agent_system/agent/agents/review/claim_agent.py)
  - [agent_system/agent/agents/review/evidence_agent.py](agent_system/agent/agents/review/evidence_agent.py)
  - [agent_system/agent/agents/review/critique_agent.py](agent_system/agent/agents/review/critique_agent.py)
  - [agent_system/agent/agents/review/general_reviewer_agent.py](agent_system/agent/agents/review/general_reviewer_agent.py)

## 四组实验模式

当前 review 任务通过 `REVIEW_MODE` 支持四种实验设置：

- `s1`：单轮单代理
- `s2`：多轮单代理
- `s3`：多轮多代理，无明确分工
- `s4`：多轮多代理，角色分工

其中 `s4` 是当前主模式，对应：

- `Review Manager Agent`
- `Claim Agent`
- `Evidence Agent`
- `Critique Agent`

模式切换逻辑在：

- [examples/drmas_trainer/run_review.sh](examples/drmas_trainer/run_review.sh)
- [examples/drmas_trainer/run_review_7b_lora_a100.sh](examples/drmas_trainer/run_review_7b_lora_a100.sh)

## 安装

如果你只是复现当前 review 任务，优先按本仓库当前可用依赖安装，不要直接把 README 理解成“已经完成 Qwen3.5 + vLLM 新版本升级”。

基础安装：

```bash
conda create -n DrMAS python==3.12 -y
conda activate DrMAS

pip install -r requirements_sglang.txt
pip install flash-attn==2.7.4.post1 --no-build-isolation --no-cache-dir
pip install -e .
```

如果你后续要切到 `Qwen3.5`，建议单独新建服务器环境，不要直接覆盖当前环境。这个升级会涉及 `vllm` 和 `transformers` 的版本重新匹配。

## 数据准备

当前 review 数据预处理脚本会把论文正文写入 `env_kwargs.paper_text`，这是多轮 `ReviewState` 版本必须依赖的字段。

执行：

```bash
python examples/data_preprocess/drmas_review.py --local_dir ~/data/drmas_review
```

输出：

- `~/data/drmas_review/train.parquet`
- `~/data/drmas_review/test.parquet`

如果你之前已经生成过旧版 review parquet，建议重新生成一次。

## 运行

如果你还在沿用原始训练入口，可以继续用：

```bash
bash examples/drmas_trainer/run_review.sh
```

评估：

```bash
bash examples/drmas_trainer/run_review.sh eval
```

常用参数：

```bash
REVIEW_MODE=s4 MAX_TURN=4 MAX_WORKERS_PER_TURN=2 bash examples/drmas_trainer/run_review.sh
```

支持的关键环境变量：

- `REVIEW_MODE`：`s1/s2/s3/s4`
- `MAX_TURN`：最大轮数
- `MAX_WORKERS_PER_TURN`：每轮最多调用的 worker 数
- `REVIEW_LOG_DIR`：多轮日志输出目录

如果你想先绕开 `verl`，直接做 inference-first 的 review 实验，现在可以直接用：

```bash
python scripts/run_review_infer.py \
  --model-path /reviewF/datasets/Qwen3___5-4B \
  --dataset-path ~/data/drmas_review \
  --split test \
  --mode s4 \
  --limit 1 \
  --max-turns 4 \
  --max-workers-per-turn 2 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.55 \
  --output-path outputs/review_infer/results.jsonl
```

这个入口不会走 `verl.trainer.main_ppo`，而是直接：

- 读取 review parquet
- 构造 `ReviewEnv`
- 用 `vllm` 调用 manager / worker agents
- 写回 `ReviewState`
- 输出最终 review、reward breakdown 和 turn logs

## 日志与可观测性

当前 review 任务已经记录多轮 turn log。每轮会保留：

- manager 决策
- 被选中的 agents
- 各 agent 的结构化 payload
- 合并后的 state snapshot
- finalize 后的 final report

相关实现位于：

- [agent_system/environments/env_package/review/envs.py](agent_system/environments/env_package/review/envs.py)
- [agent_system/environments/env_package/review/state.py](agent_system/environments/env_package/review/state.py)

## 测试

当前已补充 review 多轮基础测试：

```bash
pytest -q tests/test_review_multiturn.py tests/test_review_inference_runner.py
```

测试文件：

- [tests/test_review_multiturn.py](tests/test_review_multiturn.py)
- [tests/test_review_inference_runner.py](tests/test_review_inference_runner.py)

## 设计边界

这次改造遵守了两个边界：

- 不修改 `verl/`、PPO trainer 和 rollout collector 主循环。
- 不做框架级 structured-state 协议重构，`ReviewState` 只作为 review 任务私有黑板存在。

也就是说，当前仓库研究的是“多轮审稿辅助任务如何挂接到现有训练骨架上”，而不是重新设计整个 RL 框架接口。

## 当前状态

仓库目前已经完成：

- review env 从单轮一步终止改为多轮状态机
- `ReviewState` schema 与 merge/render 逻辑
- manager 驱动的 routing/cycle
- Claim/Evidence/Critique/General Reviewer 的严格 JSON 输出
- 多轮日志记录
- `S1/S2/S3/S4` 四种模式配置

仓库中原有的 search/math 代码仍然保留，但它们现在不是本项目 README 的主线。

## Acknowledgement

本仓库基于 [verl-agent](https://github.com/langfengQ/verl-agent) 和 [verl](https://github.com/volcengine/verl) 改造而来。当前 review 任务在此基础上做了面向论文评审辅助的多轮多智能体适配。
