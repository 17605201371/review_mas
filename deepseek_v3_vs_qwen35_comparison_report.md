## DeepSeek V3 vs Qwen3.5-9B 对比实验报告（4/8 篇论文）

> **2026-06-05 修正说明：这份报告只覆盖早期 4/8 篇 DeepSeek API 结果，不能作为最终跨模型结论。**
> 后续完整 8 样本 `local_deepseek_v3_full8.jsonl` 的同 ID 漏斗审计显示，DeepSeek 在 raw evidence payload、direct final support、fallback dependency 和 evidence_support_score 上明显优于 Qwen 9B。请优先参考：
>
> - `MODEL_TRANSFER_DIAGNOSIS_20260605.md`
> - `MODEL_TRANSFER_FUNNEL_QWEN8_DEEPSEEK_FULL8.md`
> - `MODEL_TRANSFER_FUNNEL_DEEPSEEK_16.md`

### 实验背景

本实验在多Agent论文评审系统（Dr.MAS Review）中，对比两个模型的表现：

- **Qwen3.5-9B**：本地 vLLM 推理，7轮多Agent（Manager/Claim/Evidence/Critique/General Reviewer），p0fix3 优化代码
- **DeepSeek V3**：火山引擎 API 云端推理，同样的 p0fix3 代码和 prompt 模板，max_tokens 从 640 提升到 2048

数据集：smoke8_sameids_20260604（8篇论文，same_ids 分组），目前已完成前 4 篇。

### Reward 评分机制

reward 总分 = 五大维度加权求和 - 惩罚，范围 [0, 1]。

**Content Alignment（30%）**：用 IDF 加权 token 精度，衡量生成评审与参考评审的文本对齐度。
- summary_align（5%）、strength_align（5%）、weakness_align（10%）、suggestion_align（5%）、global_align（5%）

**Evidence Support（40%）**：从 review_state 的 decision_hygiene 结构中提取，衡量证据形成质量。
- es_coverage（12%）：有真实强证据支撑的 claims 占比
- es_depth（8%）：证据深度（deep×1.0 + moderate×0.5 / claims数）
- es_empirical（6%）：有实证数据支撑的 claims 占比
- es_independent（4%）：有 2+ 独立来源支撑的 claims 占比
- es_flaw_density（6%）：有根据的缺陷数量（3个饱和）
- es_support_volume（4%）：强支撑总量（2×claims数 饱和）

**Structure（10%）**：section_presence（6%）四章节完整性 + length_score（4%）长度适当性（200-800词满分）

**Critique Density（10%）**：weaknesses 章节中的批判密度

**Stance Alignment（10%）**：预测立场（正/负/混合数值）与参考立场的距离

**Penalty**：占位符(+0.2)、过短(+0.1)、审计ID泄漏(最高0.1)

### 逐篇详细对比

#### Paper 1: hj323oR3rw

| 指标 | 权重 | DeepSeek V3 | Qwen3.5-9B | 差值(DS-QW) |
|------|------|------------|------------|-------------|
| **reward** | total | **0.3715** | **0.4605** | **-0.0890** |
| summary_align | 5% | 0.5207 | 0.5046 | +0.0161 |
| strength_align | 5% | 0.3622 | 0.3891 | -0.0269 |
| weakness_align | 10% | 0.3012 | 0.2404 | +0.0608 |
| suggestion_align | 5% | 0.2000 | 0.2000 | 0.0000 |
| global_align | 5% | 0.2836 | 0.3042 | -0.0206 |
| critique | 10% | 0.4286 | 0.4878 | -0.0592 |
| stance_align | 10% | 0.8016 | 0.7778 | +0.0238 |
| es_coverage | 12% | 0.2500 | 0.5000 | -0.2500 |
| es_depth | 8% | 0.0000 | 0.5000 | -0.5000 |
| es_empirical | 6% | 0.2500 | 0.5000 | -0.2500 |
| es_independent | 4% | 0.0000 | 0.0000 | 0.0000 |
| es_flaw_density | 6% | 0.0000 | 0.0000 | 0.0000 |
| es_support_volume | 4% | 0.1250 | 0.2500 | -0.1250 |
| evidence_support_score | 40% | 0.1250 | 0.3500 | -0.2250 |

分析：DeepSeek V3 大幅落后，主要因 evidence_support 差距巨大（0.125 vs 0.350）。es_depth 为 0（无 deep/moderate 证据），es_coverage 仅一半。

#### Paper 2: QAAsnSRwgu

| 指标 | 权重 | DeepSeek V3 | Qwen3.5-9B | 差值(DS-QW) |
|------|------|------------|------------|-------------|
| **reward** | total | **0.4682** | **0.4526** | **+0.0156** |
| summary_align | 5% | 0.3914 | 0.4643 | -0.0729 |
| strength_align | 5% | 0.3804 | 0.3394 | +0.0410 |
| weakness_align | 10% | 0.3012 | 0.2456 | +0.0556 |
| suggestion_align | 5% | 0.2000 | 0.2000 | 0.0000 |
| global_align | 5% | 0.2698 | 0.2622 | +0.0076 |
| critique | 10% | 0.7438 | 0.3015 | +0.4423 |
| stance_align | 10% | 0.8831 | 0.9464 | -0.0633 |
| es_coverage | 12% | 0.3333 | 0.5000 | -0.1667 |
| es_depth | 8% | 0.3333 | 0.5000 | -0.1667 |
| es_empirical | 6% | 0.3333 | 0.5000 | -0.1667 |
| es_independent | 4% | 0.3333 | 0.0000 | +0.3333 |
| es_flaw_density | 6% | 0.0000 | 0.0000 | 0.0000 |
| es_support_volume | 4% | 0.3333 | 0.2500 | +0.0833 |
| evidence_support_score | 40% | 0.2833 | 0.3500 | -0.0667 |

分析：DeepSeek V3 小幅领先。critique 分数极高（0.744 vs 0.302），es_independent 是唯一非零值（0.333）。但 evidence 子指标仍弱于 Qwen。

#### Paper 3: X41c4uB4k0

| 指标 | 权重 | DeepSeek V3 | Qwen3.5-9B | 差值(DS-QW) |
|------|------|------------|------------|-------------|
| **reward** | total | **0.4137** | **0.3251** | **+0.0886** |
| summary_align | 5% | 0.6256 | 0.4825 | +0.1431 |
| strength_align | 5% | 0.4116 | 0.5151 | -0.1035 |
| weakness_align | 10% | 0.2354 | 0.2852 | -0.0498 |
| suggestion_align | 5% | 0.2000 | 0.2000 | 0.0000 |
| global_align | 5% | 0.2916 | 0.3156 | -0.0240 |
| critique | 10% | 0.4865 | 0.6091 | -0.1226 |
| stance_align | 10% | 0.9509 | 0.6000 | +0.3509 |
| es_coverage | 12% | 0.2500 | 0.0000 | +0.2500 |
| es_depth | 8% | 0.2500 | 0.0000 | +0.2500 |
| es_empirical | 6% | 0.2500 | 0.0000 | +0.2500 |
| es_independent | 4% | 0.0000 | 0.0000 | 0.0000 |
| es_flaw_density | 6% | 0.0000 | 0.0000 | 0.0000 |
| es_support_volume | 4% | 0.1250 | 0.0000 | +0.1250 |
| evidence_support_score | 40% | 0.1750 | 0.0000 | +0.1750 |

分析：DeepSeek V3 明显领先。Qwen 的 evidence 全部为零（完全没形成证据），DeepSeek 至少形成了部分证据。stance_align 也远优于 Qwen（0.951 vs 0.600）。

#### Paper 4: 9zEBK3E9bX

| 指标 | 权重 | DeepSeek V3 | Qwen3.5-9B | 差值(DS-QW) |
|------|------|------------|------------|-------------|
| **reward** | total | **0.3938** | **0.4535** | **-0.0597** |
| summary_align | 5% | 0.5357 | 0.5977 | -0.0620 |
| strength_align | 5% | 0.3148 | 0.3916 | -0.0768 |
| weakness_align | 10% | 0.3395 | 0.2667 | +0.0728 |
| suggestion_align | 5% | 0.2667 | 0.2667 | 0.0000 |
| global_align | 5% | 0.3097 | 0.3799 | -0.0702 |
| critique | 10% | 0.3863 | 0.3141 | +0.0722 |
| stance_align | 10% | 0.7989 | 0.7364 | +0.0625 |
| es_coverage | 12% | 0.2500 | 0.5000 | -0.2500 |
| es_depth | 8% | 0.2500 | 0.5000 | -0.2500 |
| es_empirical | 6% | 0.2500 | 0.5000 | -0.2500 |
| es_independent | 4% | 0.0000 | 0.0000 | 0.0000 |
| es_flaw_density | 6% | 0.0000 | 0.0000 | 0.0000 |
| es_support_volume | 4% | 0.1250 | 0.2500 | -0.1250 |
| evidence_support_score | 40% | 0.1750 | 0.3500 | -0.1750 |

分析：DeepSeek V3 落后，evidence 再次弱于 Qwen（0.175 vs 0.350）。Content alignment 全面落后。

### 汇总统计

| 论文 | DeepSeek V3 | Qwen3.5-9B | 差值 | 胜出方 |
|------|------------|------------|------|--------|
| hj323oR3rw | 0.3715 | 0.4605 | -0.0890 | Qwen |
| QAAsnSRwgu | 0.4682 | 0.4526 | +0.0156 | DeepSeek |
| X41c4uB4k0 | 0.4137 | 0.3251 | +0.0886 | DeepSeek |
| 9zEBK3E9bX | 0.3938 | 0.4535 | -0.0597 | Qwen |
| **均值** | **0.4118** | **0.4229** | **-0.0111** | **Qwen** |

### 维度均值对比

| 维度 | 权重 | DeepSeek V3 均值 | Qwen3.5-9B 均值 | 差值 |
|------|------|-----------------|-----------------|------|
| Content Alignment 合计 | 30% | 0.1391 | 0.1405 | -0.0014 |
| Evidence Support | 40% | 0.1944 | 0.2625 | -0.0681 |
| Structure 合计 | 10% | 0.1000 | 0.1000 | 0.0000 |
| Critique Density | 10% | 0.5113 | 0.4281 | +0.0832 |
| Stance Alignment | 10% | 0.8586 | 0.7652 | +0.0934 |

### 关键发现

1. **总分几乎持平**：DeepSeek V3 均值 0.4118 vs Qwen3.5-9B 均值 0.4229，差距仅 -0.011（-2.6%）。一个参数量大数十倍的云端模型，在相同代码和 prompt 下几乎没有提升。

2. **Evidence Support 是最大差异源**：DeepSeek 在 evidence_support_score 上平均落后 0.068（-26%），这是 reward 中权重最大的维度（40%）。具体表现在 es_coverage、es_depth、es_empirical 三项全面落后。

3. **DeepSeek 在 Critique 和 Stance 上有优势**：critique +0.083，stance +0.093。说明 DeepSeek 确实更擅长批判性分析和立场判断，但这些优势被 evidence 劣势所抵消。

4. **Qwen 的 evidence 形成更稳定**：Qwen 在 3/4 篇论文中 evidence_support_score = 0.350（非常一致），仅 X41c4uB4k0 为 0。DeepSeek 的 evidence 则波动较大（0.125-0.283）。

5. **Prompt 可能是瓶颈**：当前 prompt 模板是针对 Qwen3.5-9B 的行为特点调优的（强化格式约束、详细指令）。DeepSeek V3 作为满血大模型，指令跟随能力远强于 9B 模型，"保姆级"prompt 可能反而过度约束了它的发挥。

6. **架构层面**：该系统的 reward 40% 由 evidence support 决定，而 evidence 质量主要由 pipeline 确定性逻辑（claim 提取、evidence 搜索验证、support tracking）决定，模型能力的影响被架构"天花板"限制了。

### 实验配置

```
模型:     deepseek-v3-2-251201 (火山引擎 API)
API:      https://ark.cn-beijing.volces.com/api/v3
max_tokens: 2048 (vs Qwen 的 640)
mode:     s4 (多角色多Agent)
max_turns: 7
max_workers_per_turn: 2
api_max_workers: 4
api_timeout: 180s
temperature: 0.2
top_p: 0.95
代码版本: p0fix3 (与 Qwen 基线完全相同)
```
