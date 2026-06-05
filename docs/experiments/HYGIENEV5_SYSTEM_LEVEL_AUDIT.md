# HygieneV5 系统层级审计：论文发表差距评估

## 1. 审计对象

- V5 主结果：`critique_hygienev5_full39_20260511_qwen35.jsonl`
- V5 指标：`hygienev5_metrics_full39.json` / `hygienev5_metrics_full39.csv`
- V5 human report meta 审计：`audit_meta_leakage_hygienev5_full39.json`
- V5 CEF 一致性审计：`audit_cef_hygienev5_full39.json`
- V4 同口径指标：`hygienev4_metrics_current_view.json`
- V4 CEF 审计：`audit_cef_hygienev4_current_view.json`

本审计只评价系统层级差距，不把 full39 当作最终论文主实验。

## 2. 一句话结论

HygieneV5 已经把 ReviewState 的结构一致性、人类报告卫生、正向 evidence 形成推进到可作为“系统卫生/可审计性”论文证据的阶段；但它距离“可发表为可靠自动审稿/可用接收拒绝决策系统”仍有明显系统层级差距。最大缺口不是单点 bug，而是：正向支持信号不能区分 gold accept/reject，负向 critique 信号过稀疏且绑定仍不可靠，final decision 仍退化为 all-reject baseline。

## 3. V5 全量结果

### 3.1 决策层

- full39 行数：39 / 39
- gold 分布（由 all-reject 下的 correctness 反推）：30 reject / 9 accept
- final decision：39 reject / 0 accept
- accuracy：30 / 39 = 0.7692
- accept recall：0 / 9 = 0
- reward mean：0.5273

这说明 V5 的最终二分类仍等价于 always-reject baseline。accuracy 不应作为主论文亮点；它只是健康检查。

### 3.2 recommendation view 层

V5 recommendation view 分布：

- `borderline_positive`：22
- `borderline_insufficient`：12
- `not_assessable_uncertain`：5
- `accept_like`：0
- `reject_like`：0

按 gold 分开：

- gold accept：4 borderline_positive / 3 borderline_insufficient / 2 not_assessable_uncertain
- gold reject：18 borderline_positive / 9 borderline_insufficient / 3 not_assessable_uncertain

若把 `borderline_positive` 当作正向信号：

- positive precision：4 / 22 = 0.182
- accept recall：4 / 9 = 0.444

所以当前 view 层能表达“支持存在”，但不能表达“是否值得 accept”。它更像 evidence richness 指标，而不是 decision-quality 指标。

## 4. V4 到 V5 的系统改善

| 指标 | V4 | V5 | 变化 |
|---|---:|---:|---:|
| accuracy | 0.7436 | 0.7692 | +0.0256 |
| final accept | 1 | 0 | 去掉 1 个 false accept |
| reward mean | 0.5215 | 0.5273 | 小幅上升 |
| real strong support | 139 | 150 | +11 |
| non-abstract strong support | 136 | 145 | +9 |
| empirical strong support | 77 | 100 | +23 |
| claims with real strong support | 67 | 68 | +1 |
| primary claim support coverage mean | 0.6154 | 0.6239 | 小幅上升 |
| primary claim empirical coverage mean | 0.3120 | 0.4316 | 明显上升 |
| flaw total | 18 | 14 | -4 |
| active flaws | 13 | 11 | -2 |
| support-only flaw filtered | 13 | 10 | -3 |
| grounded active flaws | 0 | 1 | +1，但需人工复核 |
| negative evidence candidates | 4 | 1 | -3 |
| negative evidence linked to flaw | 0 | 0 | 未改善 |
| total limitations | 269 | 254 | -15 |
| context limitations | 263 | 251 | -12 |
| open conflicts | 8 | 2 | -6 |
| recovery commits | 6 | 10 | +4 |
| CEF checks / violations | 533 / 0 | 575 / 0 | 结构一致性稳定 |

V5 的主要提升在：正向 empirical support 增强、human report 泄漏减少、state consistency 维持满分、冲突残留下降。主要未改善在：accept recall 仍为 0、负向 evidence 到 flaw 的真实绑定仍未形成。

## 5. Human-facing report 卫生

V5 meta leakage：

- sections 1-6 human-readable：1 row with L2，0 row with L1
- state field：0 leakage
- audit trace：39 rows 有 machine-readable trace，这是设计内信息，不应算 human-facing 泄漏

唯一 human-facing L2 样本：`QAAsnSRwgu`，触发词是 `snippet`，上下文是“minimal code snippets for inference”。这更像 detector false positive，而不是系统 meta 泄漏。

结论：human report 层已经接近可发表状态。后续只需把 detector 从简单 `snippet` 命中改成上下文敏感，或在报告中说明 Section 7 是 audit-only trace。

## 6. CEF / ReviewState 结构一致性

V5 CEF：

- checks total：575
- violations total：0
- aggregate consistency score：1.0

分规则：

- flaw.related_claim_ids 均可解析
- flaw.evidence_ids 均可解析
- evidence.claim_id 均可解析
- claim.supporting_evidence_ids 均可解析
- supported claim 均有 support evidence
- resolved severe flaw 均有 reason

结论：结构化 ReviewState 的 id 绑定和基本一致性已经是当前系统最强的一层，可作为论文中“state auditability / CEF consistency”的核心证据。

## 7. 正向 evidence/support 形成审计

V5 总量：

- claims：112
- evidence：246
- strong evidence：150
- support/partial_support stance evidence：238
- real strong support total：150
- empirical strong support：100
- non-abstract strong support：145

这比早期结果明显更强，但判别性不足：

| 指标均值 | gold accept | gold reject |
|---|---:|---:|
| real strong support | 3.444 | 3.967 |
| empirical strong support | 2.222 | 2.667 |
| primary claim support coverage | 0.556 | 0.644 |
| primary claim empirical coverage | 0.426 | 0.433 |
| claims with 2+ independent support | 0.333 | 0.267 |
| total limitations | 6.222 | 6.600 |
| open evidence gaps | 1.778 | 1.167 |
| flaws | 0.333 | 0.367 |

这些信号没有把 accept 和 reject 拉开。甚至 gold reject 的 support 均值略高。这说明系统现在擅长“找到支持性证据”，但还不会判断支持是否足以构成接收理由，也不会稳定发现 reject 样本的实质负面理由。

## 8. gold accept 被拒绝的 9 个样本

V5 仍然 9 个 gold accept 全部 reject。

- `hj323oR3rw`：not_assessable_uncertain，strong=0，primary_cov=0，open_gaps=4，recovery=1
- `gzqrANCF4g`：not_assessable_uncertain，strong=0，primary_cov=0，open_gaps=3
- `QAAsnSRwgu`：borderline_insufficient，strong=2，primary_cov=0.333，2plus=1，open_gaps=2
- `X41c4uB4k0`：borderline_insufficient，strong=2，primary_cov=0.667，open_gaps=1
- `BXY6fe7q31`：borderline_insufficient，strong=2，primary_cov=0.333，flaw=1，support_only_filtered=1，open_gaps=2
- `KI9NqjLVDT`：borderline_positive，strong=7，primary_cov=1.0，primary_emp=0.667，recovery=1
- `jVEoydFOl9`：borderline_positive，strong=5，primary_cov=1.0，primary_emp=1.0，2plus=1
- `LebzzClHYw`：borderline_positive，strong=1，primary_cov=0.667，2plus=1，open_gaps=2
- `1HCN4pjTb4`：borderline_positive，strong=1，primary_cov=1.0，flaw=1，support_only_filtered=1

分层看：

1. 两个 accept 样本仍没有形成任何 real strong support：这是 evidence context / evidence extraction 失败。
2. 三个 accept 样本只有 borderline insufficient：支持覆盖或独立性不够。
3. 四个 accept 样本已经是 borderline positive，但 final binary 仍 reject：这是 decision calibration / accept path 未开放的问题。

因此 accept 失败不是一个原因，而是 evidence formation、support coverage、decision calibration 三层共同导致。

## 9. 负向 evidence 与 critique 链路审计

V5 负向指标：

- paper negative evidence candidates：1
- negative evidence linked to flaw：0
- negative evidence unlinked to flaw：1
- grounded active flaw：1

关键样本：

### 9.1 `XH3OiIhtvf`

存在真实负向 evidence：

- `evidence-2-turn-4`
- claim_id：`claim-3`
- stance：`contradicts`
- strength：`weak`
- 内容：results section 没有具体实验结果，只描述 related work 和 privacy-accuracy trade-off

但最终没有任何 flaw 绑定它。说明 V5 虽然把 negative evidence 显式暴露给 Critique slice，但 Critique Agent 仍可能选择不生成 flaw，或 recovery 阶段没有把这个 negative signal 转为 grounded concern。

### 9.2 `HPuLU6q7xq`

存在唯一 grounded flaw：

- flaw title：`Unresolved Data Confidence Issue`
- negative_evidence_ids：`evidence-2-turn-2`

但该 evidence record 本身 stance 是 `supports`，不是 `contradicts`/`missing`。当前 `_flaw_has_negative_grounding` 对显式 `negative_evidence_ids` 过于信任，导致“agent 标了 negative_evidence_ids，但 evidence_map stance 不负向”的情况也能成为 grounded weakness。

这暴露两个相反问题：

1. 真实 negative evidence 可能未绑定成 flaw。
2. 非负向 evidence 可能被显式字段包装成 hard-negative grounding。

结论：负向 evidence 结构链路已经有字段和观测面，但语义验证还不够，距离论文可讲的“可靠 grounded critique”仍差一层 validator / reconciliation。

## 10. Recovery 审计

V5：

- recovery phase turns：87
- recovery commits：10
- V4 recovery commits：6

Recovery 仍大量进入，但 commits 没有带来 accept recall 或更强负向绑定。当前 recovery 更像“状态补全/保守收束机制”，还不能作为“能纠正误判”的核心论点。

论文中不能沿用早期 self-abstain dominant 叙事，也不能声称 recovery 明显提升最终判决。更安全的表述是：recovery 与 ReviewState hygiene 配合后，结构一致性稳定、冲突残留下降，但其决策收益需要单独 ablation 与人工审计。

## 11. 系统层级差距分级

### L0：基础运行与结构化状态

状态：基本达标。

证据：full39 完整跑完，CEF 575/0，id 链路稳定，state field 无 meta leakage。

剩余：需要多 seed 或更大样本确认不是 full39 偶然稳定。

### L1：Human-facing report 卫生

状态：接近达标。

证据：human sections 只有 1 个 L2，且疑似 detector false positive；L1 为 0。

剩余：正式拆分 human report 与 audit trace 的 artifact schema；修 detector 对 `code snippets` 的误报。

### L2：正向 evidence/support 形成

状态：中等偏强，但不够判别。

证据：real strong support=150，empirical strong=100，non-abstract=145。

缺口：gold accept 与 gold reject 的 support 分布几乎不可分；accept 样本仍有 2 个完全没有 strong support。

需要：Evidence Context Selection / evidence source coverage 继续做；增加 claim priority 与 contribution-level support judge。

### L3：负向 critique / grounded weakness

状态：未达发表主张要求。

证据：paper negative evidence 只有 1 个，且 0 个 linked；唯一 grounded flaw 反而来自显式字段对 supports evidence 的过度信任。

需要：negative_evidence_ids validator、stance/schema reconciliation、Critique Agent few-shot、Manager 对 unlinked negative evidence 的 binding retry。

### L4：Decision / recommendation calibration

状态：不达标。

证据：final decision 全 reject；accept recall=0；borderline_positive accept precision=0.182。

需要：不要直接调阈值；先做 decision-view evidence sufficiency model，把 accept-like 从“有支持”升级为“核心贡献有充分、独立、经验性支持，且无未解释负向证据”。

### L5：实验发表完整性

状态：full39 只能支撑 hygiene validation，不能支撑主结论。

需要：更大样本、seed、baseline、ablation、LLM judge/human judge、case study、统计显著性。

## 12. 距离论文发表的现实评估

### 如果论文定位是系统 demo / workshop / short paper

还差约 1 到 2 个系统迭代，主要补：

1. negative evidence validator + binding retry；
2. accept/recommendation view 的 audit-only calibration，不直接改 runtime threshold；
3. LLM judge 重跑 support precision / flaw grounding precision；
4. 10 到 15 个代表性 casebook。

在现有 full39 上，这条路径大约是数天到一周级工作量。

### 如果论文定位是主会 full paper，声称系统能可靠辅助接收/拒绝

还差较大。至少需要：

1. 解决 all-reject 和 accept recall=0；
2. 让 positive support / negative critique 对 gold accept/reject 有可解释区分；
3. 大样本扩展到至少 200+，多 seed；
4. 与单轮 LLM reviewer、非多智能体 reviewer、无 recovery、无 state hygiene、无 evidence context selection 等 baseline/ablation 比较；
5. support/flaw/report 三层 human 或 LLM judge；
6. recovery commit 的质量审计。

这不是再修一两个 hygiene bug 能解决的，属于 2 到 4 周级系统实验缺口。

## 13. 下一轮优先级

### P0：负向 evidence validator 与 binding retry

目标：消除“真实负向 evidence 未绑定”和“supports evidence 被显式包装成 negative grounding”的双向错误。

验收：

- `negative_evidence_linked_to_flaw_count / negative_evidence_candidate_count` 明显上升；
- explicit `negative_evidence_ids` 若 evidence stance 非负向，应降级为 potential concern 或标记 `negative_grounding_conflict`；
- grounded flaw precision 需人工/LLM judge 达到可报告水平。

### P1：Evidence Context Selection / accept 样本支持形成

目标：让 9 个 gold accept 至少不再出现 0 strong support。

验收：

- gold accept 中 real strong support=0 的样本从 2 降到 0；
- primary empirical coverage 提升；
- accept/reject support 分布开始分离。

### P2：Decision-view calibration audit model

目标：不直接调 final threshold，先建立 paper-facing sufficiency rubric。

验收：

- `borderline_positive` precision 不再低于 0.2；
- 新增 `accept_evidence_sufficiency`/`negative_risk_unresolved` 等解释性字段；
- 能解释为什么 support-rich gold reject 仍应 reject。

### P3：评估体系补齐

目标：让 full39 从调试集变成可报告验证集的一部分。

验收：

- 200+ 样本或至少多 seed；
- baseline/ablation 完整；
- LLM judge/human judge 覆盖 support、flaw、report；
- casebook 包含 accept false negative、support-rich reject、negative evidence binding、recovery commit 四类。

## 14. 最终判断

V5 可以作为“ReviewState hygiene 与 human report hygiene 明显改善”的强中间结果；不能作为“系统已经达到论文主结果可封版”的证据。当前最核心的系统差距是：系统能收集大量支持性证据，但还不能把支持性证据、负向证据、核心贡献充分性转化为可靠的审稿判断。
