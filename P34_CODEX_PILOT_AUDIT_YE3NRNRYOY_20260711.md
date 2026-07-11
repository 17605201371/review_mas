# P34 第一篇论文 Codex 辅助 Pilot 审核

## 边界

- 论文：`ye3NrNrYOY`，*Temporal Causal Mechanism Transfer for Few-shot Action Recognition*。
- 本报告是 Codex 辅助 pilot，不是独立人类金标准。
- 未写入 primary、secondary、adjudicator 标签，不参与 gate、Judge target 或 ReviewState admission。
- 判断基于 parquet 中的英文论文全文和冻结 P34 packet；中文翻译仅用于阅读。

## 总体判断

论文确实提出了 TCMT，并在 Sth-Else、HMDB-51、UCF-101、SSv2 和 5-way-k-shot
设置中给出了广泛实验。方法贡献和总体性能主张有较强原文支持；“N 消融证明模型鲁棒性”
属于提取过度。当前 10 条负向候选没有一条达到无保留的 A，5 条需要谨慎表述后成立，
2 条只适合作为弱诊断，3 条被正文反驳或过于泛化。

## 正向证据

| Packet | 建议 | 判断 |
|---|---|---|
| `positive-ye3NrNrYOY-001` | supports | 结论直接陈述提出 TCMT 及其核心机制。 |
| `positive-ye3NrNrYOY-002` | partially_supports | Figure 5 只支持单数据集、单基线的局部性能优势。 |
| `positive-ye3NrNrYOY-003` | supports | 方法章节能够支持 TCMT 框架主张。 |
| `positive-ye3NrNrYOY-004` | partially_supports | 支持 N 的影响，但不支持跨设置“鲁棒性”。 |
| `positive-ye3NrNrYOY-005` | unrelated | Figure 4 讨论更新参数数量，不是 N 消融。 |

## 主张忠实度

| Packet | 建议 | 判断 |
|---|---|---|
| `claim-ye3NrNrYOY-01` | faithful | 标题、摘要、引言和结论均明确提出 TCMT。 |
| `claim-ye3NrNrYOY-02` | faithful | 多数据集结果总体支持领先/SOTA 性能概括。 |
| `claim-ye3NrNrYOY-03` | overstated | 原文将 N 消融用于超参数选择，没有声称其证明模型鲁棒性。 |

## 负向缺陷

| Packet | 建议 | 核心判断 |
|---|---|---|
| `d874a1684f00f9` | B | 缺少适应总耗时/FLOPs；应聚焦适应成本而非笼统推理时间。 |
| `6a329686bedd72` | C | 已报告 10,000 次 5-way trial 和均值；仅 CI、方差、种子仍不足。 |
| `9e12ed6b127566` | D | Table 1 实际包含 ORViT、SViT，后续表还包含多项更广基线。 |
| `52f249e648c3c1` | B | 不变性缺少直接定量检验，但论文另有 TCMT-FT 等消融，不能说只靠可视化。 |
| `fe7d20f5557052` | B | 跨数据集不变性验证不足；与上一条同义，应合并。 |
| `6a11c6facf4c4c` | C | 单数据集 N 消融属实，但“鲁棒性”要求主要来自过度提取的 claim。 |
| `b930c99508f30b` | B | N=12 只在 Sth-Else 选择，缺少跨数据集超参数稳定性证据。 |
| `c6fa4f333494e9` | B | 已报告一批超参数和硬件，但完整架构、适应 schedule、代码仍不足。 |
| `b50fe7ea7cd5d3` | D | 论文明确报告 HMDB-51、UCF-101、SSv2 等结果，并非只评估 Sth-Else。 |
| `01b37204540a86` | D | 条件式、泛化且依赖外部知识；没有指出具体遗漏方法。 |

标签分布：`A=0, B=5, C=2, D=3`。

## 重复发现

10 条 raw candidate 实际只有 7 个 pilot 问题簇：

- `52f249...` 与 `fe7d20...`：同一“不变性验证不足”问题。
- `6a11c6...` 与 `b930c9...`：同一“N 消融跨数据集迁移”问题。
- `9e12ed...` 与 `01b372...`：高度重叠的“基线覆盖/SOTA 表述”问题。

这说明当前 `shared_cross_model_cluster_count=0` 不可信，raw candidate 数不能直接作为发现广度。
后续 precision 和 recall 应在重新聚类后的问题簇上计算。

## PaperIndex

- 6 个机器 boundary 均为真实边界，但漏掉：`2.1 GENERATIVE MODEL`、`2.2 NETWORK`、
  `3.1 EXPERIMENTAL SETUP`。
- 第一篇 boundary recall：`6/9 = 66.7%`，低于 P34 要求的 90%。
- 6 个机器 anchor 都是 exact-span，但漏掉 Tables 2-5 和作者自述 limitations。
- 按本 pilot 的 11 个关键 anchor 口径，anchor recall：`6/11 = 54.5%`。
- `preamble` 应确认是 false boundary。

## 当前结论

第一篇样本证明 discovery 已经能产生多类型、具体问题，但仍有三项关键缺陷：

1. 误报会忽略论文后续表格和完整实验段落。
2. 跨模型同义候选没有被聚类，数量被放大。
3. PaperIndex 对 subsection 和后续关键表格的召回不足，会直接影响 retrieval 和 Judge。

因此这批结果适合作为待审核 discovery，不应在人工/LLM Judge 前称为 verified negative。
