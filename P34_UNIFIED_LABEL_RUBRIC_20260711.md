# P34 统一标注 Rubric v2（七步法第①步）

日期 2026-07-11。目的：消除 P33 manual-audit 释义（"A=clear/specific/strong"）与
p34_label_contract_v1（A/B→verified 映射、A 偏直接证据型）之间的语义漂移，并终结
四类已观测的裁决病：分歧默认折中 C、A 被无规则降级 B、同类缺陷跨论文严重度漂移、
同 cluster 冲突标签。

适用：review_issue 任务（A/B/C/D）。evidence_relation 与 claim_faithfulness 沿用
contract v1 的显式 verdict 集，不在本文范围。

---

## 一、A/B/C/D(/EVR) 判定程序（按序回答，落在哪停在哪）

对**每个 cluster**（不是每条候选）依次回答：

**Q1 论文内可判定吗？** 该问题的成立与否能否仅凭论文内部内容判定？
- 否，且原因是**需要外部核查**（同期基线是否遗漏、新颖性是否成立、协议是否符合
  社区标准、是否与外部工作重复）→ **EVR**（external_verification_required）：
  这是真实的同行评审问题，**不与证据不足的 C 混类**；在未接入文献检索前不进 A/B，
  单独报告，作为系统未来外部核查能力的需求清单。
- 否，且原因是主观口味/泛化担忧等不可判定因素 → **C**（diagnostic-only，映射 uncertain）

**Q2 论文是否已直接反驳？** 全文中存在明确解决该关切的内容
（所"缺"的表/消融/说明实际存在，或断言基于误读）？
- 是 → **D**（rejected）。必须引用反驳位置（表号/节号/原文短语）。

**Q3 支持该问题的论文侧证据是什么级别？**
- 有**直接证据**：论文自己的数字/表格/协议陈述正面坐实缺陷
  （例：种子 50 vs 10 的原文、GPU vs CPU 的协议原文、参数量自相矛盾）→ **A**（verified）
- 只有**缺席证据**：经全文核查确认论文确实未提供某项，且该项对所评主张构成
  实质要求（不是任何论文都能套的通用要求）→ **B**（verified，措辞按缺席型收窄）
- 证据不足以支持上述任一 → **C**

> A 与 B 的分界只有一条：**直接证据 vs 缺席证据**。"强不强""措辞要不要小心"
> 不再是分界（那是漂移之源）。A/B 在 Judge verdict 中同为 verified，分层只用于论文表格。

## 二、paper_specificity 轴（独立于 A-D，必标）

- `paper_specific`：绑定该论文具名实体/数字/表格，换一篇论文该问题不成立
- `template_derived`：属通用审稿模板类（统计检验/复现细节/更多数据集…），但**已绑定**
  本文具体对象（如"表 1 的 +0.51% 无方差"）
- `generic`：未绑定具体对象的模板话术 → **不允许进入 A/B**；最高只能 C

计数规则：论文级 breadth 只数 `paper_specific`；`template_derived` 单独报告；
`generic` 不计入任何发现指标。

## 三、Cluster 裁决规则（先聚类后标注）

1. **cluster-first**：同义候选先合并（语义聚类 + 人工确认边界），标注对象是 cluster；
   一个 cluster **恰好一个**终标。禁止同 cluster 双标签存续。
2. **分歧裁决**：M/P 或双标注分歧时，裁决者必须按 Q1-Q3 重新走程序并**引用论文证据**
   落到明确标签。**禁止以"存在分歧"为由默认 C**——C 只能由 Q1/Q3 的证据状态产生。
3. **降级留痕**：任何 A→B、B→C 等降级必须写明触发的 Q 编号与证据；无理由降级视为无效。
4. **同类一致性**：同一 issue_type 的严重度锚点固定——
   例："缺统计显著性检验"默认 C（Q3 证据不足），仅当论文声称的增益幅度小于可疑噪声
   且以该增益为核心主张时升 B；"缺消融"默认走 Q2 全文核查后按 Q3 判 B 或 D。

## 四、与 Judge verdict 的映射（contract v1 兼容 + EVR 扩展）

| rubric | Judge target |
|---|---|
| A / B | verified |
| C | uncertain |
| D | rejected |
| EVR | uncertain（带 `external_verification_required=true` 标记，单独统计） |

## 五、生效与追溯

- 本 rubric 为 `p34_label_rubric_v2`；后续标注/裁决/gate refresh 均引用此版本号。
- 已有 377 条诊断标签**不追溯改标**，仅作诊断集；正式金标准从 v2 起重标
  （先 cluster 去重——七步②——再按本程序标注）。
- 双标一致率、kappa、分歧裁决记录按 annotation 基础设施既有流程产出。
