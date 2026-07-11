# P34-2B 弃答机制修复 + 修正版 2×2 实验设计（v2，含 GPT 交叉审核修正）

日期 2026-07-11。作者 Claude；v2 依 GPT 交叉审核 7 条修正。
状态：**机制已实现**（gate v2 输出可接入流水线的 enriched/filtered packets，
窗口 exact-span round-trip 213/213 全通过）；2×2 待跑。诊断标签非金标准。

## 一、要解决的问题（全部已验证）

1. **配额填充**：对称 discovery 40/40 槽位恰好 5 条（M 20×5=100、P 20×5=100），
   prompt 允许零弃答但**无一行使**——上限被当成任务目标。
2. **缺席幻觉**：38+/59 假阳性是"声称缺 X 而 X 在论文里"——12k 摘录判全文缺席的
   合同性缺陷。
3. **精度测量被污染**：只要凑数行为存在，任何 arm 的 precision 差异都会被回填候选压缩。

## 二、机械门的免费验证结果（决定设计走向的实证）

用已有 200 packets + 377 诊断标签，零 API 成本验证"纯机械自审门"：

| 方案 | D 杀掉 | B 保住 | 结论 |
|---|---|---|---|
| strict 机械门（anchor+confidence+实体·标记共现） | 20/59 | **46/105** | **双向失败，禁用于 admission** |

误杀样本核查：被杀 B 的"反证窗口"实为 related-work 提及/巧合共现/讨论句——
**正则能检索窗口，不能判定"窗口是否解决关切"**（与 P33 numeric verifier 同一堵语义墙，
第二次实证）。anchor 门只杀了 3 个 B、0 个 D（packets 上游已做 span 校验，冗余）。

**设计结论与实现状态（gate v2，已落地）**：
- 机械层做且只做：**字段结构校验**（forward contract：缺 searched_sections /
  absence_check_terms / confidence = 结构无效，`--require-self-audit-fields`）与
  **exact-span 检索附证**（enrich：top-k 窗口带 `source_span_start/end` + 原文切片
  quote + paper_text sha256 + section_id + matched_marker，round-trip 可机核）。
- **裁决必须是 LLM Judge**：带 quote 回填核验的封闭式 refute 判断。
- 流水线输出：`--out-packets-jsonl`（enrich=全量增强包 / strict=过滤集）+
  `--out-dropped-jsonl`（strict 淘汰清单）。strict 仅作对照 ablation，禁入 admission。
- 工具：`scripts/p34_candidate_self_audit_gate.py`；测试
  `tests/test_p34_candidate_self_audit_gate.py`（13 项：enrich 不删、strict 过滤输出、
  round-trip、缺字段、大小写 join、空文本、重复 packet、label join 完整性）。

## 三、弃答机制（结构性，非提示词恳求）

1. **候选级必填自审字段**（生成合同变更）：`searched_sections`、`absence_check_terms`、
   `confidence`，缺字段=结构无效（机械可判的是**字段存在性**）。
   **字段真实性不由自报保证**：harness 必须记录**真实检索 trace**
   （实际执行的 section/artifact 检索 ID、实际 query、命中与未命中范围、
   候选级 emit/abstain 决策及理由），自报字段仅作合同格式，不作弃答证据。
2. **relaxed-cap 组**（更名，原"无上限"不准确）：cap=12 只是更高上限；
   若产量再次贴顶 12/12，自然产量仍未知——**贴顶率必须显式上报**，
   贴顶时结论只能写"产量 ≥ cap"，不得当自然分布。
3. **低缺陷对照**（修正，不再假设"强论文≈零问题"）：
   用**人工预核的低缺陷对照论文**或**构造的 negative-control claims**；
   指标报 **false-positive propensity**（对照集上的产出率），不假设真值为零；
   对照样本量按可负担扩到 ≥3 篇/组。
4. **防"全弃答刷分"**：指标必须同时含 precision + coverage + **有效簇绝对数** +
   对照集误报率——四者联合，弃答换不来免费高分。

## 四、修正版 2×2（v2：Judge 恒定，只切 CE bundle）

**四组全部经过同一个固定 Judge（同模型、同 prompt、同 schema）**；
唯一组间差异 = AuditPacket 里是否附 CE evidence bundle（gate v2 的
`counterevidence_windows`）。A→B 的增益因此**只**归因于反证证据的存在。

| 组 | Discovery | AuditPacket 内容 | Judge |
|---|---|---|---|
| A | MiMo | 基础包（packet 自带 top-7 检索） | 固定 Judge |
| B | MiMo | 基础包 + CE bundle（enrich 窗口） | 同一 Judge |
| C | MiMo-Pro | 基础包 | 同一 Judge |
| D | MiMo-Pro | 基础包 + CE bundle | 同一 Judge |

其余不变：discovery 上下文/prompt 四组恒定；反证链=发现后的候选级增强；
全组启用第三节弃答机制。

主要指标（全部 cluster 级）：cluster precision、D 率、paper-specific 率、template 率、
**贴顶率与自然产量分布**、对照集 FP propensity、重复率、强问题数、有效簇绝对数。
判读同前：A→B 大=反证证据主因；A→C 大=模型能力主因；D 最好=都要；D 仍差=重定义问题。

## 五、执行顺序（并入七步法）

```
gate v2（已完成：enrich/strict 输出 + exact-span 窗口 + 13 测试）
  → 七步① 统一 rubric v2（含 external_verification_required）   ← 已完成
  → 七步② cluster 去重硬门（每 cluster 一个终标）
  → 修正版 2×2（本文四节；开跑前需人工确认低缺陷对照集）
  → 七步③ claim 轻量门 / ④ absence 反证主路径（B/D 组机制常驻化）
  → 七步⑤ specificity 轴（rubric 内已含）/ ⑥ agreement 分层抽检
  → 七步⑦ cluster 级 P34-2 正式盲测
```

红线继承：人工标签不进 runtime；模型判断必须过 quote 回填；诊断标签不作金标准；
每 smoke 一个因子；`state_contamination=0` 等不变量保持。
