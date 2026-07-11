# P34 双模型共识版：全流程发现、审核与恢复计划

日期：2026-07-11

共识来源：

- `P34_FULL_PIPELINE_LLM_AUDIT_REFACTOR_PLAN_20260711.md`
- `P34_FULL_PIPELINE_AUDIT_AND_LLM_VERIFIER_PLAN.md`
- `P34_CROSS_MODEL_AUDIT_FOR_CLAUDE_20260711.md`
- `P34_CLAUDE_REVIEW_OF_GPT_PLAN_20260711.md`

本文是后续实施的统一主计划。原文件继续作为审计依据，不覆盖、不撤回。

## 一、论文目标与能力边界

目标论文不是单独的负向缺陷检测器，而是完整的 multi-agent peer-review discovery and verification system：

```text
论文输入
  -> Claim 抽取
  -> 正向 Evidence 搜集
  -> Free-form Critique 缺陷发现
  -> 支持/反证/缺失项证据包
  -> Cross-model LLM Judge
  -> ReviewState admission
  -> Contested relation
  -> Guarded Recovery
  -> State-grounded final report
  -> Independent Report Audit
```

目标贡献：

1. 结构化 ReviewState 统一组织 claim、正向证据、负向问题、冲突和恢复生命周期。
2. MiMo-2.5 与能力更强的 MiMo-2.5-Pro 在 discovery 与 verification 角色上进行对称交叉实验，区分 discovery 能力、self-judge 偏差和 cross-model judge 增益。
3. 所有模型判断必须绑定可定位的论文证据、检索范围和 counterevidence；模型一致本身不构成 verification。
4. Recovery 至少保证非破坏和零污染；只有经过 Judge 复核的一致性改善才计为有效修正。
5. 最终报告从审核后的状态生成，并经过独立一致性审核。

当前不能提前声称：

- 134 hypotheses 已代表经过验证的主结果。
- 当前 main episode 已实现 free-form discovery。
- 当前人工 admission 已被机器 Judge 替代。
- 当前 Recovery 已证明能改善一致性。
- 当前 accept/reject 或 reward 能代表真实审稿质量。

## 二、当前已确认的问题

### P0：数据入口字段错配

数据集真实字段为：

```text
inputs / outputs / year / id / mode / rating / decision / reviewer_comments
```

runner 未直接读取 `outputs`、`decision` 和 `rating`，导致完整 reference review、ground-truth decision 和 reference ratings 缺失。

`reviewer_comments` 当前会进入 reward fallback，因此不能表述为“所有人工评审文字均未使用”；准确结论是完整 `outputs` 没有进入 reference review，decision/rating 指标结构性失真。

### P0：主 episode 的 discovery 上下文不足

- Manager 论文片段约 700 字符。
- Claim Agent 上下文约 2.2k 字符。
- Evidence Agent 常规总观测约 3.6k-4.2k 字符。
- Critique Agent 总观测约 4.2k 字符。
- hardneg20 论文约 17k-64k 字符。

P33 probe 使用约 12k 字符战略摘录、最终 claims/evidence/inventory、free-form prompt、8 hypothesis 上限和 temperature 0.0，产生 134 hypotheses。该结果证明 MiMo 具有发现潜力，但不是上下文长度的单因子证据。

### P0：Agent 角色和字段权限混乱

- Claim Agent 在 Evidence/Judge 前写 support status。
- Claim obligations 会成为后续缺陷模板来源，存在循环自证风险。
- Manager schema 可写 claims/evidence/flaws/final report。
- Evidence 同时承担正向搜证、负向验证和 free-form discovery。
- 普通 worker 可以覆盖相同 ID claim/flaw 的多数业务字段。

### P0：负向验证信任根仍是人工

修正 paper-id 问题后，`machine_grounded=60/60`，无法区分人工 A/B/C/D。Grounding 只能证明文字或实体存在，不能证明缺陷关系成立、counterevidence 不存在或问题具有审稿价值。

### P0：main episode 与 P33 sidecar 不闭环

- free-form discovery 在 sidecar。
- semantic/contract/admission 在后处理脚本。
- admission 在 report/reward 之后。
- 主 runner 只追加 3 evidence 和 3 contested relations，17 cases 被跳过。
- admission 后未重新运行真实 multi-turn Recovery。

### P1：状态容量和历史留存不足

- claims/flaws 最多保留 8 条。
- evidence 最终最多保留 12 条。
- retention 对正向 support 略有偏好，`missing` evidence 可能被挤出。
- revision log 最多 40 条；hardneg20 的 20 个状态全部撞上限。

### P1：Recovery 只证明安全，没有证明有效

- `recovery_consistency_improved=False` 为 127/127。
- patch 主要来自 `system_salvaged`。
- state contamination 和 harmful commit 保持 0，这是应保留的安全贡献。

### P1：最终输出和评测目标错位

- 20/20 final decision 为 reject，但 grounded weakness 为 0。
- 10 篇在 turn budget 结束。
- report、reward 和 post-admission state 版本不一致。
- report 仍可能泄漏 agent/state/recheck 等内部语言。
- verified negative 在总 reward 中最高约占 6%，正向支持相关分量约占 34%。
- decision score 不进入 total；rating alignment 被计算但不进入 total。

## 三、核心架构

### 1. PaperIndex

PaperIndex 保存全文和可审计的结构化定位：

```text
PaperSection
  section_id
  section_type
  heading
  text
  source_span_start
  source_span_end
  parent_section_id

PaperArtifact
  artifact_id
  artifact_type: table | figure | equation | caption | list
  locator
  text
  source_span_start
  source_span_end
```

最小接口：

```text
PaperIndex.search(query, section_types, top_k)
PaperIndex.get_section(section_id)
PaperIndex.get_span(start, end)
PaperIndex.coverage(expected_section_types)
```

PaperIndex 不依赖单一正则。优先使用 LaTeX/Markdown heading、environment、caption 和段落结构；无法稳定解析时保留顺序 chunk fallback，并明确标记解析置信度。

硬验收基于人工标注的 expected anchors，而不是要求每篇固定存在 method/results/table：

- expected section boundary recall >= 90%。
- method/result/table/caption 关键 anchor retrieval recall >= 90%。
- false section boundary rate <= 10%。
- 任意返回 span 必须能在原始 `paper_text` 唯一定位。
- 20 篇逐篇输出 parser mode、失败原因和 fallback 使用情况。

### 2. Agent 字段所有权

| 数据 | 唯一模型写入方 | 最终确认方 |
|---|---|---|
| claim text/source/type | Claim Agent | Claim Judge + deterministic span verifier |
| claim obligation proposal | Claim Agent | Claim Judge |
| evidence quote/locator | Evidence Agent | deterministic quote verifier |
| issue hypothesis | Critique Agent | Review Issue Judge |
| support/negative relation | 无普通 Agent 写权限 | LLM Judge |
| severity/actionability | Critique proposal | Review Issue Judge |
| verified grounding | 无模型写权限 | deterministic verifier |
| contested relation | 无普通 Agent 写权限 | Admission/Recovery layer |
| route/finalize proposal | Manager | deterministic controller |
| final user report | State renderer | Report Auditor |

非字段所有者的更新必须拒绝并记录 `authority_violation`，不能静默覆盖。

### 3. Judge 类型

统一使用与候选生成角色分离的结构化 verdict，但按任务拆分 prompt：

```text
ClaimFaithfulnessVerdict
  faithful | overstated | unsupported_extraction | uncertain

EvidenceRelationVerdict
  supports | partially_supports | contradicts | unrelated | uncertain

ReviewIssueVerdict
  verified | rejected | uncertain

RecoveryVerdict
  improved | no_effect | harmful | uncertain

ReportConsistencyVerdict
  pass | fail
```

所有 verdict 记录：

```text
accepted_evidence_ids
counterevidence_ids
searched_section_ids
confidence
rationale
judge_model
judge_version
prompt_version
state_version
```

### 4. AuditPacket

Judge 不接收只有一面信息的候选。标准包为：

```text
claim
claim_source_spans
supportive_evidence
contradictory_evidence
issue_hypothesis
observed_inventory
missing_or_weak_items
searched_sections
counterevidence_candidates
unsearched_scope
```

Judge 可以请求一次补充检索，但不能自己生成不存在的引用。引用、locator 和 span 必须由程序重新核验。

## 四、双模型交叉审核实验

模型：

- `mimo-v2.5`：当前主生成模型，记为 M。
- `mimo-v2.5-pro`：更强的主审核/对照模型，记为 P；通过现有 `MIMO_API_KEY` 和 `MIMO_BASE_URL` 直接调用。
- 新增 `MIMO_PRO_MODEL` 配置项；默认使用 MiMo API 实际支持的 Pro model id，并在 guard smoke 中验证 model id、response format、token 参数和超时行为。
- DeepSeek 不再是主双模型之一，保留为可选的跨供应商 external-control Judge，用于检查同家族模型的相关性偏差。

模型独立性口径：

- M 与 P 是不同能力等级的模型，但同属 MiMo 家族、共用同一 API provider，不能表述为完全独立供应商审核。
- 论文主实验使用 `cross-model judging` 或 `model-separated judging` 表述。
- 若加入 DeepSeek external control，才可额外报告跨供应商 Judge 的稳健性结果。

核心 2x2：

| 组 | Discovery | Judge | 目的 |
|---|---|---|---|
| M-M | MiMo | MiMo | MiMo self-judge baseline |
| M-P | MiMo | MiMo-Pro | 更强 cross-model Judge 增益 |
| P-P | MiMo-Pro | MiMo-Pro | MiMo-Pro self-judge baseline |
| P-M | MiMo-Pro | MiMo | 反向交叉审核 |

附加基线：

| 组 | Discovery | Verification |
|---|---|---|
| RULE | deterministic menu/checklist | deterministic grounding |
| M-P-CE | MiMo | MiMo-Pro + explicit counterevidence retrieval |
| M-EXT | MiMo | optional DeepSeek external-control Judge |

实验约束：

- 所有组使用同一 PaperIndex、AuditPacket、taxonomy 和输出 schema。
- Judge 看不到 generator identity。
- 同一模型 self-judge 时不得获得 generation 阶段隐藏内容。
- 所有候选先去重和 cluster，再计算 precision/recall，避免多写同义候选刷数量。
- 双模型 agreement 只作分析指标，不直接触发 admission。
- 每个 Judge 对固定 AuditPacket 至少重复两次，报告 test-retest agreement。

主要回答：

1. 增益来自更强 discovery，还是更强 Judge？
2. Independent Judge 是否优于 self-judge？
3. MiMo 与 MiMo-Pro 的错误是否相关，是否存在同家族确认偏差？
4. Counterevidence retrieval 是否减少假阳性？
5. 模型分歧是否集中在特定 issue type？
6. 可选 external-control Judge 是否与 MiMo-Pro 得到一致结论？

## 五、实施阶段与 Go/No-Go

### P34-0A：修复 dataset ingestion

- `inputs` -> paper input。
- `outputs` -> reference review。
- `decision` -> ground-truth decision。
- `rating` -> reference ratings。
- `reviewer_comments` 继续保留为评论和 fallback reference。
- 删除默认 user goal 中强制 accept/reject 的要求。

验收：

- 20/20 行正确加载全部真实字段。
- decision/rating/reference 指标重新计算。
- dashboard 明确标记旧结果为 pre-fix，不与新结果混用。

### P34-0B：上下文单因子实验

固定：

- model。
- temperature。
- prompt/schema。
- ReviewState snapshot。
- max hypotheses。
- max output tokens。

只改变：

- 3.6k context。
- 8k context。
- 12k strategic excerpt。
- PaperIndex section-aware retrieval。

指标：valid JSON、specific rate、人工 precision、type breadth、paper coverage、cost 和 latency。

该实验只确定上下文的边际贡献，不直接作为论文主结果。

### P34-1：功能完整的 PaperIndex 与字段权限基础

- 建立可同时服务盲测和后续 runtime 的完整 PaperIndex，不以“最小改动”为约束。
- 支持 LaTeX/Markdown section、顺序 chunk fallback、table/figure/caption/equation artifact、唯一 span 定位、检索 coverage、缓存和 parser provenance。
- 新增字段 authority validator 和明确的写入权限；新链路中直接拒绝越权更新，旧主链通过 feature flag 保持可回滚。
- 将 Claim、Critique、Evidence 和 Judge 的检索统一建立在 PaperIndex 上，避免为旁路和 runtime 维护两套不同上下文逻辑。
- 输出逐篇 section/anchor coverage、fallback、检索命中和错误报告。
- 允许对相关模块进行必要的结构性重构；不为了追求小 diff 保留明显重复或冲突的四条负向 lane。

Go 条件：PaperIndex 达到第三节硬验收。

### P34-2：双模型 Judge 旁路盲测

开发集：

- hardneg20 的已有 60 条负向 hypotheses。
- 至少 80 条正向 claim-evidence pairs。
- Claim faithful/overstated 样本。
- Recovery 和 final report consistency 样本先用于 schema smoke，不用于主门槛。

人工标签要求：

- 明确 A/B/C/D 定义。
- 至少一部分样本双人标注。
- 报告一致率和分歧裁决。
- 在计算 Judge precision/recall 前冻结人工标签文件并记录内容 hash；Judge prompt、输出和 gate 不得读取人工标签。

Discovery provenance 硬约束：

- 每个 review-issue AuditPacket 必须在 Judge 不可见的冻结 sidecar 中记录真实 discovery model。
- `discovery_code` 不能只是运行参数或结果组名；runner 必须据 provenance 选择对应候选。
- 同一个跨模型 issue cluster 可以同时属于 M/P，但 Judge 可见 packet 中不得出现 generator identity。
- P provenance 缺失时，P-P/P-M 必须在任何 API 请求前阻断，禁止把 M 候选改名为 P 候选。

负向 Go 条件：

- precision >= 80%。
- A/B verified recall >= 30/37。
- D verified leakage = 0/9。
- A/B/D adjudication coverage >= 80%。
- C -> uncertain 单独报告，不纳入 coverage 下限。
- verified 绝对数必须报告。

正向 Go 条件：

- claim-evidence relation accuracy >= 85%。
- accepted quote/span locatability = 100%。

稳定性 Go 条件：

- JSON/schema success >= 99%。
- cross-model Judge macro-F1 至少领先对应 self-judge 8 个百分点，或提供统计置信区间证明稳定优势。
- 固定 AuditPacket test-retest agreement >= 85%。

No-Go：任一硬门槛失败，Judge 不获得 runtime admission 权限，系统继续保持 human-in-the-loop 定位。

门槛解释：

- `D verified leakage = 0/9` 只作为 hardneg20 开发阶段的工程 Go/No-Go，不得写成论文级“零假阳性”结论。
- 论文级泛化结论必须由冻结配置后的 19 篇 paper-level holdout 支持。
- P34-2 不是唯一风险来源；人工金标准可靠性和 PaperIndex anchor recall 是进入 Judge 盲测前必须通过的前置门。

运行顺序：

1. 先在 3 篇 paper/API guard sample 上运行 M-M、M-P、P-P、P-M，验证 MiMo API model id、schema、quote/span 回填和重复调用稳定性。
2. guard sample 通过后，再运行完整 hardneg20 开发集。
3. guard sample 只用于排除技术失败，不用于报告最终模型能力。

### P34-3A：episode shadow integration

- 接入 Claim/Evidence/Issue Judge 调用，但 verdict 只写 shadow audit，不改变 live ReviewState。
- 对比 shadow verdict 与当前 deterministic/manual gate。
- 记录额外成本、延迟、失败率和状态差异。

### P34-3B：Judge admission activation

仅当 P34-2 全部门槛通过：

- `verified` 且 deterministic grounding 通过的关系进入 verified state。
- `uncertain` 进入 pending layer。
- `rejected` 只保留审计记录。
- admission 发生在 report/reward 之前。
- admission 后继续真实 Critique/Recovery turns。

### P34-3C：人工 runtime gate 移除

仅当 P34-3B 在 hardneg20 完整运行稳定：

- 人工 A/B/C/D 从 bridge、semantic、contract、bundle 和 admission runtime 逻辑退出。
- 人工文件只用于离线评测。
- feature flag 默认保持可回滚。

### P34-4：ReviewState 留存与版本一致性

- claim/evidence/issue/verdict 使用 immutable provenance。
- 每次 admission/recovery 产生新 `state_version`。
- evidence retention 按 claim coverage、正负平衡、独立来源和 verdict 分组。
- `missing`、`contradicts` 和 counterevidence 不得无声淘汰。
- revision history 完整保存；prompt 只消费压缩摘要。
- report、reward、state_audit 和 returned state 必须引用同一版本。

### P34-5：Recovery 双层目标

核心必达安全目标：

- `state_contamination=0`。
- `recovery_harmful_commit_risk=0`。
- `recovery_no_effect_commit=0`。
- verified actionable concern 不被破坏。

增强有效性目标：

- RecoveryVerdict 判定 `improved`。
- 目标冲突减少。
- 未损害其他 verified relations。
- recovery 后 final-view 与状态一致。

`system_salvaged` 只计安全兜底，不计 agentic recovery success。

若有效性目标失败，论文仍可保留 non-destructive recovery safety 贡献，但不得声称自主修正能力。

### P34-6：Final Report Auditor

- 最终报告只从 Judge-audited ReviewState 生成。
- Manager final report 降级为内部 draft，不覆盖结构化摘要。
- 每条 strength/weakness/concern/limitation 绑定 verdict 和 evidence lineage。
- Report Auditor 检查无证据主张、状态矛盾、严重度错误、重要 issue 遗漏和内部术语泄漏。
- Auditor fail 时回退确定性 renderer。
- accept/reject 只作可选派生字段，不作核心论文结果。

### P34-7：Reward 与评测

当前 reward 降级为工程诊断。先不直接提高负向权重，避免诱导强行制造缺陷。

论文主指标：

- Claim faithfulness precision/coverage。
- Positive relation accuracy、support depth、independent support coverage。
- Negative discovery precision/recall/type breadth/paper coverage/actionability。
- Judge calibration、adjudication coverage、test-retest agreement。
- Recovery safety/effectiveness。
- Report factual consistency 和 process-language leakage。
- API cost、latency、token、turn count 和 budget exhaustion。

Judge 指标稳定后，再单独设计训练 reward，使其与 relation accuracy、verified issue、Recovery 和 hygiene 对齐。

## 六、开发集与真正盲测

### hardneg20

用途：

- 数据修复验证。
- prompt/schema 开发。
- PaperIndex 验收。
- Judge 校准。
- 消融和 failure analysis。

不得作为最终 generalization 证据。

### full39 剩余 19 篇

流程：

1. 在 hardneg20 上冻结代码、prompt、taxonomy、threshold、model config 和 admission policy。
2. 计算并记录配置 hash。
3. 只运行 full39 中未包含在 hardneg20 的 19 篇。
4. 不根据结果调整任何门槛。
5. 人工在运行结束后盲审。

Holdout 失败时如实报告，不回到 hardneg20 继续调整后重复宣称同一批为盲测。

### P34 Experiment Lock

新增 `scripts/p34_experiment_lock.py`，在任何 holdout API 调用前创建和验证不可变实验锁：

- 读取真实 parquet，验证 hardneg20 为 20 个唯一 paper、full39 为 39 个唯一 paper、交集恰为 20、差集恰为 19。
- 冻结 hardneg20/full39 数据文件 hash 和完整 20/19 paper ID 列表。
- 冻结 PaperIndex、retrieval、field authority、runner/state、prompt、symmetric discovery、Judge、2×2 和 label-audit 关键文件 hash。
- 冻结不含 API key 的模型配置：provider/base URL、M/P model id、temperature、top-p、token/context/hypothesis budget、repeat 和 bootstrap 数量。
- 冻结全部 Go/No-Go threshold 和 readiness artifact hash/status。
- 记录 git HEAD、branch 和 dirty entry count；finalize 模式可要求 clean worktree。
- `--verify-manifest` 会重新检查代码文件、数据集、readiness artifact、模型配置和 manifest 自身 config hash；任一变化返回 `DRIFT_DETECTED`。
- 只有五个 readiness 门全部通过且可选 clean-git 条件满足时，`--finalize` 才产生 `FROZEN_READY`；否则明确返回 `BLOCKED_NOT_FROZEN`。

当前 draft lock：

```text
P34_EXPERIMENT_LOCK_DRAFT_20260711.{json,md}
status = DRAFT_BLOCKED
hardneg/full/holdout = 20/39/19
config_sha256 = 见锁文件（避免在被锁主计划中形成自引用 hash）

P34_EXPERIMENT_LOCK_DRAFT_VERIFY_20260711.{json,md}
status = PASS
mismatch_count = 0
```

当前 finalization check 正确拒绝冻结，原因包括：2×2 BLOCKED、PaperIndex
`NEEDS_MANUAL_ANCHORS`、positive/claim label BLOCKED、symmetric discovery BLOCKED，
以及 clean-git 模式下工作树未清洁。该 draft hash 只是当前状态快照，不得用于宣称配置已经正式冻结。

### P34 Holdout Label-Sealed Bundle

full39 原始数据同时包含 `inputs` 和 `outputs/decision/rating/reviewer_comments`。即使 paper ID
split 正确，直接把原 parquet 交给 holdout runner 仍会留下 reference leakage 风险。新增
`scripts/p34_holdout_bundle.py` 强制执行字段与权限隔离：

- 只有 `FROZEN_READY` 且重新验证无漂移的 experiment lock 才能物化 holdout。
- 重新验证 full39 hash、锁内 19 个 holdout ID、与 hardneg20 零交集。
- public execution parquet 只包含 `id/inputs/year/mode`。
- `outputs/decision/rating/reviewer_comments` 单独写入 sealed JSON，文件权限设为 `0600`。
- public input 禁止出现 reference、rating、decision、reward_model、extra_info 等字段。
- bundle manifest 冻结 lock/config/full39/public/sealed hash、19 个 ID、列清单和文件权限。
- verify 模式重新检查 experiment lock、config hash、public/sealed 文件 hash、19 个唯一 ID、禁止列和 sealed 权限；任何变化返回 `DRIFT_OR_LEAKAGE_DETECTED`。
- ndarray/list 等 parquet 字段按结构化 JSON 类型保存，不转换成不可逆字符串。

当前使用 draft lock 的真实授权检查：

```text
P34_HOLDOUT19_CURRENT_20260711_REPORT.{json,md}
status = BLOCKED
reason = experiment_lock_not_finalized
public input written = false
sealed references written = false
```

因此当前系统不仅“约定不跑 holdout”，而是在 final lock 前无法生成可执行 holdout 数据文件。

## 七、执行顺序

1. P34-0A：dataset ingestion 修复。
2. P34-0B：上下文单因子实验。
3. 冻结 hardneg20 原始结果、人工标签和实验配置 hash。
4. P34-1：实现功能完整的 PaperIndex、统一检索接口和字段 authority 基础。
5. P34-2 guard：3 篇 M-M/M-P/P-P/P-M API/schema smoke。
6. P34-2 full：hardneg20 双模型 2x2 Judge 旁路盲测。
7. 执行正式 Go/No-Go；未通过则停止所有 runtime admission、Recovery、Report Auditor 和 reward 重构。
8. P34-3A：episode shadow integration。
9. P34-3B：Judge admission activation。
10. P34-3C：人工 runtime gate 移除。
11. P34-4：ReviewState retention/version consistency。
12. P34-5：Recovery safety/effectiveness。
13. P34-6：Final Report Auditor。
14. P34-7：完整评测和后续 reward 设计。
15. 冻结配置，运行 19 篇 paper-level holdout。

资源红线：P34-2 正式 Go 之前，不实施 P34-3B/3C，不投入 P34-4 及之后的 Recovery/Report/reward 重构。P34-0/P34-1 允许按功能完整性进行必要的结构调整，不以最小改动为目标。

## 八、最终论文主张边界

只有在 holdout 达标后才能声称：

- Multi-agent system autonomously discovers cross-type review issues。
- Cross-model judging between MiMo-2.5 and MiMo-2.5-Pro verifies claim-evidence and review-issue relations without runtime human labels；同家族模型限制必须如实报告。
- ReviewState preserves an auditable positive/negative evidence lifecycle。
- Guarded Recovery is non-destructive；若有效性指标通过，再声称能够改善一致性。
- Final reports remain traceable to verified state relations。

无论结果如何都不得声称：

- 双模型 agreement 本身等于真实性。
- 未经 precision 审核的 134 hypotheses 是 verified discoveries。
- evidence 不足自动意味着 reject。
- deterministic system salvage 等于 agentic recovery。
- hardneg20 开发结果等于 blind generalization。

## 九、执行进度（2026-07-11）

| 阶段 | 状态 | 当前结论 |
|---|---|---|
| P34-0A | 完成 | hardneg20 20/20、full39 39/39 canonical ingestion 通过 |
| P34-0B | 完成 | 8k context 相对 3.6k 有正边际，12k 未继续稳定增益 |
| P34-1 PaperIndex | 功能完成，硬验收待定 | 20/20 span 回映、0 fallback；人工 anchor 文件未冻结，不能判 Go |
| P34-1 authority | 功能基础完成 | `off/shadow/enforce` 已实现；enforce 使用显式字段白名单，Claim/Evidence 只进入 pending proposal 队列，不污染 live state |
| P34-2 guard | PASS | V4 固定 AuditPacket：Pro discovery 3/3，Judge 12/12 + 24/24，四组 test-retest 100% |
| P34-2 full | 未开始 | 等待 PaperIndex 人工 anchor、80+ 正向 pair 和冻结标签/hash |

最新技术 guard：

```text
P34_2_DUAL_MODEL_JUDGE_GUARD3_API_V4_FIXED_PACKET_20260711.{json,md,log}
```

V4 明确执行了一次 bounded supplemental retrieval，并在同一个增强后
AuditPacket 上重复两次最终审核。3 篇 MiMo 候选覆盖人工 A/B/D。manual-D
样本在 M-M 中稳定 verified、在 M-P 中稳定 rejected，这是支持 cross-model
Judge 研究问题的方向性信号，但不得替代 hardneg20 full precision/recall。

### P34-2 数据集与能力 Pilot 更新

统一数据集已经构建：

| 类型 | 数量 | 当前标签状态 |
|---|---:|---|
| evidence relation | 104 | 待人工主标注与部分双标 |
| review issue | 60 | A/B/C/D 人工标签已冻结 |
| claim faithfulness | 73 | 待人工主标注与部分双标 |

所有 237 个 packet 的引用均可回映原始 `paper_text`。旧 ReviewState 中的
positive evidence offset 是清洗后正文偏移，P34 已全部重新定位，不能复用旧 offset。

12-case A/B/C/D pilot 的三次有效结果：

| 版本 | 主要改变 | M-P precision | M-P A/B recall | D leakage | 结论 |
|---|---|---:|---:|---:|---|
| V1 | 初版 full runner | 0.60 | 0.60 | 2/4 | No-Go |
| V2 | defect polarity + matched window | 无 verified | 0.00 | 0/4 | 过度拒绝，No-Go |
| V3 | verification contract | 0.7143 | 1.00 | 2/4 | 召回恢复但精度未过，No-Go |

V4 已加入 `paper_internal_verifiability` 和正式 capability gate，用于阻止
依赖外部文献、社区标准或现实普遍性的 hypothesis 被当成 paper-internal verified
defect。V4 尚无结果：MiMo 主 Key 余额不足，备用 Key 与主 Key 相同，HTTP 402
发生在有效样本产生前。不得把该执行失败记为模型能力结果。

### P34-2 2×2 discovery provenance 修正

后续审计确认，原 237-packet 数据集中的 60 个负向 candidate 全部来自 P33/MiMo，
但旧 `p34_judge_runner.py` 的 `--discovery-code P` 只改变组名，不改变 packet 来源。
因此旧基础只能合法支持 M-M/M-P，不能支持 full P-P/P-M；此前 guard 的 Pro discovery
3/3 只覆盖三篇技术 smoke，不能外推为 hardneg20 Pro discovery 集。

现已完成结构性修正：

- Judge dataset schema 升级为 `p34_judge_dataset_v2`。
- 新增 `P34_2_JUDGE_DATASET_HARDNEG20_20260711_NEGATIVE_DISCOVERY_PROVENANCE.json`。
- 旧 60 个负向 packet 的真实 provenance 为 `M:60, P:0`；packet hash 不变。
- Judge runner 强制读取 provenance；以旧数据运行 P 组会在 API 前返回
  `no_review_issue_packets_for_discovery_code:P`，请求数为 0。
- provenance 仅在 sidecar；Judge prompt 和 AuditPacket 均看不到 generator identity。

新增 `scripts/p34_symmetric_discovery.py` 建设真正的 full 2×2 discovery 输入：

```text
同一 hardneg20 paper set
  -> 同一 PaperIndex strategic context（12k）
  -> 同一 free-form prompt/schema/max_hypotheses
  -> M 与 P 分别生成
  -> 模型内去重
  -> 跨模型 issue clustering
  -> neutral AuditPacket
  -> hidden discovery provenance sidecar
  -> blinded A/B/C/D human audit
```

跨模型发现同一 issue 时只生成一个中性 cluster packet，sidecar 记录
`discovery_codes=[M,P]`，避免人工重复审核和同义候选刷数量。A/B/C/D 冻结后会自动映射为
`verified/uncertain/rejected` 目标，直接供 Judge scorer 使用。

工程验收：

```text
P34_2_SYMMETRIC_DISCOVERY_DRYRUN_HARDNEG20_20260711
papers = 20
request slots = 40 (20 M + 20 P)
prompt/context symmetry = true
generator identity absent from packets = true

P34_2_SYMMETRIC_DISCOVERY_GUARD1_API_20260711
papers = 1
M request = HTTP 402
P request = HTTP 402
status = BLOCKED_API（不是模型能力结果）
```

因此 P34-2 full 的真实前置现在是：余额恢复后先生成 M/P 对称 discovery 集，完成其
blinded A/B/C/D 主标和双标，再运行 M-M/M-P/P-P/P-M Judge；不能直接在旧 60 packet 上跑四组。

### P34-2 统一 2×2 编排与总闸

新增 `scripts/p34_2x2_experiment.py`，将恢复余额后的正式实验收敛为单一入口，避免四个
局部命令使用不同 packet、label 或 provenance：

- 基础数据只取 positive evidence relation 和 claim faithfulness，不混入 legacy M-only review issue。
- 负向数据只取 `p34_symmetric_discovery.py` 生成的 neutral review-issue packets。
- 先验证三类 task、M/P provenance、所有人工标签、重复 ID 和原文 span，再决定是否调用 API。
- M discovery 运行 M-M/M-P，并共享执行正向 Evidence/Claim Judge；P discovery 运行 P-P/P-M review-issue Judge。
- 仅使用两次重复均合法且 verdict 一致的 packet 计算指标。
- 输出每组 confusion matrix、observed-class macro-F1、test-retest、schema success、verified 绝对数、A/B recall、D leakage、A/B/D coverage 和 C→uncertain。
- 输出 cluster-level discovery precision、A/B 有效 cluster 数、paper coverage、issue-type breadth 和 M/P shared cluster 数。
- 对 M-P vs M-M、P-M vs P-P 使用同一 packet 的配对 bootstrap：只有 self/cross 两组都完成固定次数复审且各自 verdict 稳定的 packet 才进入重采样；标签类别固定为完整配对样本的 observed classes。
- 默认 2000 次 deterministic bootstrap，输出 paired packet 数、self/cross macro-F1、差值和 95% CI。
- 正式总闸检查 M-P precision/recall/D/coverage、positive relation accuracy、test-retest、schema success；cross-model review-issue macro-F1 必须点估计领先至少 0.08，或配对 bootstrap 95% CI 下界大于 0。P-M 与 P-P 的反向差值和 CI 单独报告。
- 门槛由独立 `P34_2_GATE_CONTRACT_20260711.json` 冻结并纳入 experiment lock；正式 report 记录 contract SHA-256。合同缺失、schema/字段缺失、非法 rate/count、D leakage 非零或 bootstrap 类别被删减时，在任何 API 请求前阻断。
- preflight 同时强制开发集样本基数：evidence relation 至少 80；review issue 至少 A/B=37、D=9、C=1。比例门不能由缩小分母绕过。
- A/B recall 与 A/B/D coverage 的分母是对应 discovery group 的全部预注册 gold packet；schema failure、缺失 repeat 和 test-retest 不一致均按未召回/未覆盖处理，不再从分母中消失。
- verified precision 覆盖 A/B/C/D 的全部稳定 verified 输出，C 被错误判为 verified 会降低 precision；C→uncertain 仍独立报告，不进入 A/B/D coverage。
- 除 recall rate 外，M-P 必须绝对 verified 至少 30 个 A/B；paired bootstrap 至少 30 个共同稳定 packet，并同时覆盖 verified/rejected/uncertain 三类。
- positive evidence decisive verdict 必须引用合法 `accepted_evidence_ids`，结合 preflight exact-span roundtrip 计算 accepted quote/span locatability，门槛为 100%。
- Judge blinding 不再依赖 `labels_withheld_from_prompts=true` 自我声明。每批 initial/final prompt 都反序列化末尾 `AuditPacket`，与对应 neutral packet 做 exact hash/equality 比较，并递归拒绝任何 label/reviewer/annotator/adjudicator、target verdict、discovery code/model/source-candidate 字段。
- prompt blinding manifest 只保存 title/prompt/packet SHA-256、exact-match 和泄漏路径，不保存额外 prompt 副本；request ledger 仍只以 prompt SHA-256 建 key，不保存 raw prompt。initial 泄漏在 ledger/API 前阻断，supplemental final 泄漏在对应 final API 前阻断。

当前真实 preflight：

```text
P34_2_2X2_PREFLIGHT_CURRENT_20260711_REPORT.{json,md}
status = BLOCKED
packets = 177 (positive 104 + claim 73)
review_issue packets = 0
M discovery packets = 0
P discovery packets = 0
missing human labels = 177
invalid source spans = 0
API calls = 0
gate contract schema = p34_2_gate_contract_v1
minimum cardinality blockers = A/B 0/37, D 0/9, C 0/1
```

该阻断证明编排器不会在缺少对称负向或人工金标准时生成空的、重命名的或不可比较的 2×2 表格。

### P34-2 完整四组仿真验收

旧 6-packet synthetic 能验证编排可达，但会让比例门在极小分母上通过，不能证明真实 Go/No-Go 语义。现将 deterministic acceptance 升级到完整门槛规模：

- 使用 141 个冻结 AuditPacket：80 个 evidence relation、1 个 claim faithfulness、60 个 M/P shared review issue；负向人工 gold 分布固定为 A=1、B=36、C=14、D=9，并提供完整 label contract、provenance 和可回映 paper span。
- 同时运行 M-M、M-P、P-P、P-M，固定两次 final repeat；synthetic P Judge 稳定命中 target，M Judge 稳定翻转 review verdict，使 cross-model gain、precision/recall、D leakage、coverage 和 positive accuracy 门均被真实计算。
- decisive positive verdict 均引用 exact-span evidence ID；C 类稳定输出 uncertain；M-P paired bootstrap 覆盖 verified/rejected/uncertain 且共同稳定 packet 不少于 30。
- 首次执行通过统一 request ledger 精确产生 1206 个 request，四组 metrics 完整，aggregate Go/No-Go 为 `PASS`。
- 使用相同配置再次执行时 1206/1206 cache hit、API request=0、fake provider call=0，证明 M/P 两个 discovery run 共享 ledger 时不会碰撞、漏跑或重复付费。
- 删除 gate contract 的第三次执行在 provider call 前返回 `BLOCKED`，API request=0、fake provider call=0。
- 1206 个 synthetic 请求的 initial/final AuditPacket 均 exact roundtrip，M/P 两个 discovery run 的 prompt blinding audit 均为 `PASS`；注入嵌套 `human_reviewer_id`、`human_label` 或 `discovery_code` 的回归样本会在 provider call 前 `BLOCKED`。

该仿真只证明编排、schema、指标和续跑功能可达，不作为任何模型能力结果；正式 P34-2 仍必须等待真实人工金标准与 MiMo API。

### P34-1 字段权限加固更新

字段权限已从“normalize 后审计”前移到模型原始 JSON，并补齐完整 proposal 生命周期基础：

- Manager 的实体写入在原始 payload 层拒绝并保留 violation provenance。
- Claim 合法抽取字段进入 `pending_claim_proposals`，support status 和 supporting evidence relation 被拒绝。
- Evidence 合法 quote/locator/span 字段进入 `pending_evidence_proposals`，stance、strength、binding、grounding 和 support-quality verdict 被拒绝。
- 受控实体内未登记字段默认拒绝，不能通过新增嵌套字段绕过 authority contract。
- pending proposal 进入 ReviewState 的独立队列，但不进入 live `claims` / `evidence_map`；普通 Agent 只看到 pending 数量，不获得 Judge 权限。
- 默认 `DRMAS_FIELD_AUTHORITY_MODE=off`，旧链保持可回滚；P34-2 Go 前不激活 Judge admission。

历史 hardneg20 原始 payload 在新白名单口径下仍有 `215/264` 个有效越权 payload；
Evidence 的违规事件增至 `449`，主要是旧 prompt 要求其同时写 stance、strength、binding、grounding
和 support-quality verdict。这是迁移工作量，不是新系统错误率。

### P34-2 API 失败可审计性更新

`p34_judge_runner.py` 现在会捕获供应商/API 失败并写出结构化 `BLOCKED` 报告，
保留阶段、Judge code、错误类型、expected/valid counts 和 blocking issues，不再因 traceback
丢失整轮实验记录。最新 1-packet MiMo-Pro 余额探测仍为 HTTP 402：

```text
P34_2_MIMO_PRO_BALANCE_PROBE_20260711.{json,md}
initial_valid = 0/1
final_valid = 0/2
status = BLOCKED（原因是 API balance；运行阻塞，不是模型能力结论）
```

### P34-1 统一角色检索进度

`PaperIndex` 已从 Evidence-only shadow 接入升级为统一的 role-aware retrieval：

- Claim：优先贡献、方法、结果和边界主张。
- Evidence：按 target claim、evidence need、结果、分析和方法检索。
- Critique：优先结果、分析、限制、反证、统计和可复现性。

三角色共享 span/provenance/cache，但 query plan 和 section priority 不同。

| 角色 | 非空 | span roundtrip | required-group coverage | section-type recall |
|---|---:|---:|---:|---:|
| Claim | 20/20 | 20/20 | 0.9667 | 0.8775 |
| Evidence | 20/20 | 20/20 | 0.9500 | 0.8208 |
| Critique | 20/20 | 20/20 | 0.8750 | 0.7542 |

三角色 result set 在 20 篇中仅 2 篇完全相同，说明角色化不是表面改名。
该结果记为 `PASS_FUNCTIONAL`，但人工 section boundary / anchor gate 仍为
`NEEDS_MANUAL_ANCHORS`，二者不得混用。

### P34-2 人工金标准 readiness

已用正式 audit 工具重新量化总闸前置，不把空模板或 machine prelabel 当人工标签：

| 标注集 | 总数 | 已主标 | 已双标 | 当前状态 |
|---|---:|---:|---:|---|
| positive evidence relation | 104 | 0 | 0/20 minimum | BLOCKED |
| claim faithfulness | 73 | 0 | 0/15 minimum | BLOCKED |
| PaperIndex human anchors | 20 papers | 0/20 complete | n/a | NEEDS_MANUAL_ANCHORS |

对应 readiness 报告：

```text
P34_2_POSITIVE_HUMAN_LABEL_READINESS_20260711.{json,md}
P34_2_CLAIM_HUMAN_LABEL_READINESS_20260711.{json,md}
P34_1_PAPER_INDEX_AUDIT_HARDNEG20_20260711.{json,md}
```

PaperIndex audit 已修正一个假阳性：仅存在 20 个模板 case 不再计为
`all_papers_annotated=true`；必须逐篇设置 `human_review_complete=true` 且提供真实
boundary/anchor/false-boundary 标签。当前正确口径为 `completed_annotation_count=0/20`，
只有 `all_spans_roundtrip=20/20` 通过。

### P34 人工审核工作台

为真正解除人工金标准阻塞，已实现本地可持久化审核工作台：

```text
server = scripts/p34_annotation_server.py
ui = scripts/p34_annotation_app.html
url = http://127.0.0.1:8765
output_dir = P34_ANNOTATIONS_20260711/
```

功能边界：

- 直接加载冻结的 237 个 AuditPacket，不重新生成或改写 packet。
- 正向 evidence relation 104 条和 claim faithfulness 73 条均展示 claim、候选证据、来源和 counterevidence context。
- 新增负向缺陷页，读取对称 discovery 输出，展示 hypothesis、resolution evidence、counterevidence query 和检索证据，使用 A/B/C/D 主标与双标。
- `primary` 与 `secondary` 独立落盘，可直接输入 `p34_human_label_audit.py` 做一致率、Cohen kappa 和分歧裁决。
- 新增独立 `adjudicator` 模式，只展示 primary/secondary 均已完成且标签不一致的 packet；并排显示双方标签与理由，裁决结果单独写入 `<task>_resolution.json`，不覆盖任何原始标注。
- 冻结标签时，非空且相同的双标才计为 `double_agreement`；双方都为空不能伪装成一致，分歧未裁决也不能进入 frozen gold。
- PaperIndex 逐篇展示 machine boundary/anchor/false-boundary suggestions；机器建议必须由审核者显式勾选，不能自动成为人工标签。
- PaperIndex 只有至少确认一个 boundary 和一个 anchor 后才能设置 `human_review_complete=true`。
- 所有结果使用原子 JSON 写入，支持页面刷新和进程重启后恢复。
- 服务启动时即物化三类任务的 primary/secondary/resolution 文件和 PaperIndex primary/secondary 文件（共 11 个固定 audit 输入）；只创建缺失文件，绝不覆盖已有人工标签。
- 支持未完成筛选、paper/packet 搜索、进度统计、主标/双标切换和移动端布局。

浏览器验收：三种任务加载成功；实际双标保存使进度 `0/104 -> 1/104`；实际分歧流程完成了 primary、secondary、adjudicator 三方保存，并验证比较面板、理由和 resolution 落盘；所有浏览器测试标注随后均已删除。390px viewport 无横向溢出。工作台解决标注执行工具缺失，但金标准完成度仍保持真实的 0，不得把工具完成误写为标注完成。

### P34 独立人工审核者身份门

仅用 `primary/secondary/adjudicator` 角色名不能证明存在两个或三个独立审核者。正式标注链现已加入不可变身份注册：

- `annotator_registry.json` 将每个角色首次绑定到明确的 `reviewer_id`；同一角色不能改绑，同一 ID 不能占用第二个角色。
- reviewer ID 不再只是客户端声明。首次绑定同时生成一次性 256-bit 角色 token；浏览器仅在本地保存明文，服务端 registry 只保存 SHA-256，label、resolution、bundle 和实验报告均不包含 token。
- label、resolution 和 PaperIndex anchor 每次保存都必须携带与注册表一致的 ID，服务端拒绝缺失或错配身份。
- 保存、PaperIndex、审核包导出和审核包导入均要求 reviewer ID 与 token 同时匹配；知道另一个审核者的 ID 不足以冒用其角色。
- `p34_human_label_audit.py` 在正式 gate 中要求所有已完成 primary 标签来自唯一审核者、所有 assigned secondary 标签来自另一个唯一审核者；若存在分歧，resolution 必须来自第三个不同审核者。
- 角色名兼容模式仅由显式 `--allow-role-only-identity` 开关提供给旧测试/迁移场景，正式 annotation server 与 gate refresh 默认强制真实身份。
- 前端完成状态只认服务端确认过的保存。错误身份请求被拒绝时保留当前草稿，但进度和侧栏仍显示“待审核”，避免 optimistic UI 伪造完成度。

隔离浏览器验收已证明：`reviewer-a` 绑定 primary 后不能绑定 secondary；`reviewer-b` 可独立绑定 secondary；使用错误 ID 保存被拒绝且进度保持 `0/20`；改回正确 ID 后保存为 `1/20`，页面刷新后注册表与标签均恢复。认证升级后，浏览器首次绑定可正常保存，registry 为 `p34_annotator_registry_v2`、token hash 长度 64、无明文 token；无 token 的保存与审核包导出均被拒绝。390px viewport 的 document/body width 均为 390，无横向溢出。QA 使用临时 output directory，正式人工标签仍为 0。

### P34 独立审核交换包

为使两名审核者和第三方裁决者能够在不共享浏览器会话、彼此标签或本机目录的情况下并行工作，工作台新增结构化导出/导入：

- 每次只导出当前 `task × role` 的盲化审核包；primary 与 secondary 包只包含各自可见 packet 和本角色草稿，不包含另一人的标签或理由。adjudicator 仅在真实分歧存在时看到双方结论。
- secondary 导出严格使用冻结 assignment；当前 evidence 包为 20 条、覆盖 19 篇，不会退化为自行挑选全量 104 条。
- `bundle_sha256` 同时绑定 task、role、reviewer ID、assignment hash、template hash、完整 packet contract 和导出时本角色 label-state hash。
- 回收请求只上传标签区，不回传大体积论文上下文；服务端用当前 packet/assignment/template 重新计算 bundle hash，拒绝错角色、错 reviewer、缺失/重复 packet、非法标签、已过期 assignment 和旧标签状态。
- 批量导入先校验全批，再按任务一次性原子写入；任一行失败时不允许半批落盘。导入成功后的旧包不能再次覆盖更新结果。
- UI 提供“导出/导入”命令，仍由服务端身份门和 frozen assignment 决定可见范围，不信任客户端文件自报。

真实隔离验收：secondary evidence 包大小 130,602 bytes，20/20 packet、19 papers、0 primary 字段；批量回收 20 行后只有 1 个非空标签，进度精确为 `1/20`；篡改 hash 返回 400，进度保持不变。390px viewport 下新增命令未造成横向溢出。QA 目录随后清理，正式标注仍为 0。

### P34 单文件离线审核台

JSON 交换包虽然安全，但要求审核者手工编辑结构化文件，不足以支持真正的独立并行标注。现新增 `scripts/p34_portable_annotation.html`：

- 在线工作台“导出”会在通过 reviewer token 认证后生成一个自包含 HTML，而不是裸 JSON。packet、allowed labels、bundle hash 和当前本角色草稿以 base64 嵌入，避免论文文本打断脚本或注入 HTML。
- 离线文件无需 Python、服务端或网络，可完成搜索、未完成筛选、逐条导航、任务专用 evidence/claim/issue 展示、标签选择、理由填写和进度统计。
- “导出结果”只生成原 schema 的 labeled JSON；审核者 token 不进入离线 HTML，也不进入回传 JSON。中心工作台导入时仍重新执行身份认证、bundle/label-state hash 校验和原子批量写入。
- 离线模板不引用 CDN、字体、外部脚本或图片，不包含 `fetch`、`XMLHttpRequest`、`WebSocket`、`http://` 或 `https://`，也不使用浏览器持久化存储保存论文内容。
- 模板本身纳入 experiment lock，冻结后不能通过修改离线标签语义绕过实验配置。

真实 primary evidence 离线包包含 104 items/104 labels，大小 893,000 bytes，marker 全部替换、网络依赖命中 0、明文认证 token 0，并包含本地结果下载逻辑。应用内浏览器策略禁止自动打开 `file://`，因此此处只声明自包含结构和数据契约已验证，不把它误写为离线视觉自动化通过；在线工作台的 390px 布局仍已实际通过。

### P34 PaperIndex 离线交换与批量校验

PaperIndex 原先仍只能在中心工作台逐篇操作，导致最关键的 `0/20` human-anchor gate 无法像其他三类标签一样分发。现已完成同等级的离线链路：

- `p34_paper_index_exchange_v1` 绑定 role、reviewer、anchor-template hash、当前 case-state hash、20 篇 paper text 和全部 machine boundary/anchor/false-boundary suggestions。
- 专用 `scripts/p34_portable_paper_index.html` 提供全文查看、机器建议勾选、boundary/anchor/false-boundary 人工新增编辑删除、备注、完成声明、搜索、未完成筛选和结果导出。
- 回收时要求 paper ID 与当前 20 篇 workspace 精确一致；所有 cases 先统一清洗和验证，完成项必须满足 heading/source window、anchor exact text/span 和 false-boundary source match，随后才一次性原子写入。
- 在线单篇保存和离线批量导入共享 `_prepare_anchor_case`，不存在两套完成语义；任一 case 失败时整批不落盘。
- Bundle hash 包含导出时的 case-state，成功导入后旧离线包自动失效，不能覆盖更新后的 anchor 标注。
- 专用模板和通用离线模板均纳入 experiment lock。

真实 hardneg20 验收：20 papers/20 cases 单文件大小 1,217,542 bytes；首篇原文 34,961 字符；无未替换 marker、网络调用、外部 URL 或明文 token。采用首篇真实 machine boundary 与 anchor suggestion 后一次回收 20 cases，exact-span 验证通过，临时进度精确为 `1/20`。QA 目录随后删除，正式 PaperIndex 仍保持 0/20。

### P34 Reviewer 级离线任务包

为避免审核者逐任务导出并遗漏文件，工作台新增“导出全部”：

- 一次 token 认证后，按角色收集全部当前可见任务。primary 包含 evidence、claim、存在时的 review issue 和 PaperIndex；secondary 只包含 frozen assignment 可见的 label tasks，并可带自己的 PaperIndex 工作区；adjudicator 只包含当前真实分歧任务。
- ZIP 内每个任务仍是独立 HTML 和独立 bundle hash，不把多个任务合并为一个信任边界；`manifest.json` 记录 task、schema、item count、bundle hash 和 HTML hash。
- ZIP 使用固定文件顺序、固定 timestamp、固定权限和 deterministic compression；相同状态重复导出必须 byte-identical。
- Package contract 绑定 role、reviewer、assignment 和所有文件 manifest；token 不进入 ZIP。
- 在线“导入”支持同时选择多个 labeled JSON，逐个调用各任务的认证 importer，并汇总文件数和条目数；任一任务仍保持自己的 stale-state 和原子写入保护。

真实 primary hardneg20 package：784,751 bytes，包含 claim 73、evidence 104、PaperIndex 20；当前 symmetric review issue 为空，因此未生成空文件。连续两次导出 SHA-256 均为 `62fe3ba6...ba12`，字节完全一致；manifest 中每个 HTML hash 均复算通过，明文 token 0。390px 在线布局 document/body width 均为 390，无横向溢出。

### P34 人工提交 Ed25519 完整性

Reviewer token 只能保护 API 请求。原 HMAC 方案把验签密钥与标签放在同一 workspace，同一目录读权限会削弱信任隔离，因此已升级为 Ed25519：

- 服务端私钥默认位于 `~/.config/drmas/p34_annotation_ed25519_private.pem`，目录权限 `0700`、私钥 `0600`；workspace 只保存 `annotation_signing_public.pem`，权限 `0644`。
- API 单条保存、离线批量导入和 adjudicator resolution 均对人工字段、role、reviewer、task 与 packet ID 生成 `p34_annotation_ed25519_v2` 签名。
- PaperIndex signature 覆盖 paper ID、boundary、anchor、false-boundary、完成状态、备注、role 和 reviewer；机器 suggestion 更新不改变已签人工字段语义。
- Positive/claim/negative human-label audit 与 PaperIndex gate 只读取公钥；服务停止并移走私钥后仍可独立验签。
- 缺公钥、缺签名、直接修改、跨 packet/role 复制、旧签名重放或公私钥不匹配均 fail-closed。空模板不要求签名。
- 私钥不进入 workspace、标签交换包、role ZIP、frozen labels、readiness artifact、experiment-lock config 或论文输出；readiness 报告记录公钥 SHA-256，lock 冻结验签后的 artifact hash。
- OpenSSL 3.x 是该签名层的显式运行依赖；不可用时服务启动或 gate 验签直接失败，不降级回 HMAC。

真实隔离验收：签名为 88 字符 base64。服务停止并移走私钥后，仅凭 workspace 公钥仍 `1/1 PASS`；直接修改 label reason 后准确识别 packet `positive-ye3NrNrYOY-001` 并转为 `BLOCKED`。另一个私钥不能静默替换现有 workspace 公钥。正式公钥 SHA-256 为 `f2ebcae7...e013`。

工作台输出现已直接驱动正式 positive/claim readiness、PaperIndex audit 和 2×2 preflight；当前真实结果仍为 positive 0/104、claim 0/73、PaperIndex 0/20、177 个 packet 缺人工标签、0 invalid spans、0 API calls。

Experiment lock 额外冻结 annotation server/UI、human-label audit、PaperIndex audit、Judge dataset builder、role retrieval audit 和 lock implementation 自身，防止配置冻结后通过修改金标准生成或标注语义绕过实验锁。

### P34 标注到总闸统一刷新

新增 `scripts/p34_annotation_gate_refresh.py`，将人工工作台之后的所有离线步骤收敛为一个结构化入口：

- 从固定 workspace 读取 positive、claim、negative 的 primary/secondary/resolution，分别重算完整性、一致率、Cohen kappa、未裁决分歧和 frozen labels。
- 用 primary PaperIndex anchors 重算 boundary recall、anchor recall、false-boundary rate 和逐篇完成度。
- 使用 workspace-derived frozen labels 重跑 provenance-safe 2×2 preflight；该入口硬编码 `run_api=false`，只做总闸刷新，不会消耗模型额度。
- 依次重建 draft lock、验证 lock、执行 finalize check 和 holdout authorization check，并输出单一聚合报告。
- 所有输出原子写入；任一标签不完整、分歧未裁决、span 错误、对称 discovery 缺失或锁漂移均 fail-closed。
- 该刷新脚本自身纳入 experiment lock，避免冻结后修改 gate 编排语义。
- 工作台新增只读 `/api/gates` 和显式 `/api/refresh-gates`；页面可直接显示 positive、claim、PaperIndex 进度及总闸状态。刷新总体返回 `BLOCKED` 时仍视为正常实验状态，不伪装成服务错误。

当前真实聚合报告：`P34_ANNOTATION_GATE_REFRESH_20260711.{json,md}`。状态为 `BLOCKED`，`run_api=false`；positive 0/104、claim 0/73、negative 0/0、PaperIndex 0/20、2×2 missing labels 177、invalid spans 0；draft lock verification 为 PASS，finalize/holdout 正确拒绝。

### P34 对称 Discovery Canonical Activation

新增 `scripts/p34_activate_symmetric_discovery.py`，在模型生成与人工标注之间建立不可跳过的 active artifact 层：

- 只有 manifest、packet、provenance、human template、cases 全部存在才可激活。
- 正式激活要求 `PASS_GENERATION`、20 篇、M/P 双模型均有候选、prompt 对称、packet 不泄露生成器身份、invalid span=0。
- packet/template/provenance ID 集必须完全一致；重复 ID、非 review_issue packet、packet/provenance hash 漂移均阻断。
- 通过后原子复制到 `P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711*`；2×2、gate refresh、experiment lock 和标注服务只消费 active 层，不直接消费任意临时 prefix。
- 为当前 API 402 状态提供显式 `ACTIVE_BLOCKED_BOOTSTRAP`，仅用于初始化 canonical 空路径；该状态仍不能通过 symmetric discovery readiness。
- 工作台 `/api/reload-discovery` 可热加载 active packet/template/provenance。匹配 packet 的旧标签保留，已消失 packet 的标签和 resolution 写入 `orphaned_labels/orphaned_resolutions`，不会静默删除或错误迁移。

当前 active bootstrap 来自 guard1：packet/provenance/template 均为 0，source manifest 仍为 `BLOCKED`，activation 报告为 `ACTIVE_BLOCKED_BOOTSTRAP`；工作台真实热重载返回 `RELOADED` 且 0 orphan。

### P34 对称 Discovery 一键 Pipeline

新增 `scripts/p34_symmetric_discovery_pipeline.py`，将余额恢复后的操作收敛为单一状态机：

1. 使用相同 M/P prompt、context、schema 和参数运行 symmetric discovery。
2. `DRY_RUN` 只生成 candidate artifacts，绝不改变 active。
3. API 失败或 manifest 非 `PASS_GENERATION` 时返回 `BLOCKED_DISCOVERY`，上一版 active 保持不变。
4. 只有 activation 为 `ACTIVE_READY` 才替换 canonical active artifacts。
5. 激活后调用工作台 `/api/reload-discovery`，再运行离线 gate refresh。
6. 全部成功且 packet>0 时返回 `READY_FOR_HUMAN_LABELS`；服务不可用或 gate refresh 异常分别保留为 reload/gate pending，不伪装成模型失败。

真实 hardneg20 dry-run：20 papers、40 valid M/P slots、0 candidate、状态 `DRY_RUN_COMPLETE`；active manifest SHA256 在运行前后均为 `3eb21e4f...ce3cb`，证明 dry-run 不会覆盖当前 canonical 结果。

### P34 冻结双标 Assignment

新增 `scripts/p34_annotation_assignment.py`，消除 secondary 自行挑选“容易样本”的便利抽样风险：

- 使用冻结 seed 对 packet 和 paper 做 hash 排序，以 round-robin 方式优先扩大 paper coverage，再补足目标数量。
- primary 始终审核全量；secondary 只看到 manifest 中的精确 packet ID。
- assignment 冻结三类 template hash、目标数量、实际数量、逐 paper 分布和整体 hash。
- human-label audit 要求所有 assigned secondary 完成，拒绝未分配 packet 的额外双标，并只在冻结 assignment 上计算 agreement/kappa。
- gate refresh 和 experiment lock 将 assignment 作为独立 readiness；非 `PASS` 不能 finalize。
- symmetric discovery pipeline 在 active 激活后自动重建 assignment，先热重载 assignment，再热重载 discovery，保证负向 secondary 从第一条开始就是预注册样本。

当前真实 assignment：

| Task | Primary | Frozen secondary | Paper coverage | 状态 |
|---|---:|---:|---:|---|
| evidence relation | 104 | 20 | 19 papers | 子任务可执行 |
| claim faithfulness | 73 | 15 | 15 papers | 子任务可执行 |
| review issue | 0 | 0/20 | 0 papers | BLOCKED，等待正式 discovery |

整体 assignment 状态保持 `BLOCKED`，因为负向 0/20；工作台 secondary 页面真实验收为 evidence `0/20`、claim `0/15`、review issue `0/0`，未再暴露全量 104/73。

### P34 PaperIndex 零 False-Boundary 语义修正

复核发现旧 gate 要求 `false_total > 0` 才能进入 ready，因此即使 20 篇人工完整复核并确认 parser 没有任何 false boundary，也会永久得到 `false_boundary_rate=None`，无法 PASS。现已修正：

- 未完成人工复核时，零 false-boundary 仍为 `None`，不能通过。
- 所有论文完成复核且人工明确没有 false boundary 时，rate 定义为 `0.0`。
- 只要人工标出的 false boundary 被 parser 当成真实 section，仍按 `hit/total` 计算；例如 1/1 为 `1.0` 并 FAIL。
- PaperIndex ready 不再要求人为制造至少一个 false-boundary 样本，但仍要求全篇完成、boundary/anchor 均有人工标签且 recall 达标。
- 页面完成声明改为“已逐项核对 boundary、anchor 与 false boundary”，使空 false-boundary 列表具有明确人工确认语义。

三类回归分别证明：未完成空模板 `NEEDS_MANUAL_ANCHORS`；完整零误边界 `PASS, rate=0.0`；真实误边界 `FAIL, rate=1.0`。当前 hardneg20 仍为 0/20，三个 rate 均为 `None`，没有被误放行。

### P34 PaperIndex 完整人工编辑与源文本校验

旧工作台只能勾选机器 suggestion，不能新增或修正人工项；当 parser 漏掉真实结构时，审核者无法完成标注。现已补齐：

- boundary、key anchor、false boundary 均支持新增、编辑和删除人工项。
- 机器 suggestion 被采用后进入同一个人工编辑器，可修正 heading/type/query/text/span，不再是不可编辑的机器标签。
- 草稿可以保存未完成字段；只有勾选完成时执行严格结构校验。
- 完成 boundary 必须包含 heading、section type、非负 start，且 heading 出现在原文对应窗口。
- 完成 anchor 必须包含 query、exact text、合法 start/end，并满足 `paper_text[start:end] == text`。
- false boundary 若填写，必须包含 heading、reason、合法 start，且 heading 与原文位置一致。
- 服务从 hardneg20 原始 parquet 加载 paper text；校验不是依赖 UI 自报。

同时修复 machine anchor suggestion 的 span bug：旧模板使用 240 字 preview，却保留完整 artifact end，导致勾选机器建议也无法通过 exact span；现在 `end=start+len(preview)`，首条真实建议验证为 240/240。保存文件中的旧 machine suggestion 不再覆盖新模板，人工选择和备注保留，机器字段随模板更新。

隔离浏览器验收：手工新增 boundary/anchor、填写真实 source span、完成保存、刷新恢复成功，进度 `1/20`；390px 下 document width=390、editor width=362、overflowing controls=0。QA 输出已清理，真实标注仍为 0/20。

### P34 统一 Label Contract

审计发现 positive/claim 模板缺少 `task_type`，旧 frozen labels 仅对 A/B/C/D 写 `target_verdict_mapping`，正向与主张依赖隐式“human_label 即 Judge target”。现统一为 `p34_label_contract_v1`：

- evidence relation 显式映射到 `supports/partially_supports/contradicts/unrelated/uncertain`。
- claim faithfulness 显式映射到 `faithful/overstated/unsupported_extraction/uncertain`。
- review issue 的 A/B/C/D 映射保持 `verified/verified/uncertain/rejected`。
- frozen row 必须包含 packet、paper、task type、human label、allowed labels、target verdict、label source、reason 和 contract version。
- human audit 可从 legacy allowed-label schema 推断任务，但正式 gate refresh 总是传入 expected task，并阻断源 task 冲突或任何 unmapped label。
- Judge scorer 对三类任务统一优先消费显式 `target_verdict_mapping`。
- 2×2 preflight 对所有已完成标签验证 contract version、task equality 和 target 是否属于对应 `TASK_VERDICTS`；隐式、错任务或越界 target 均阻断。
- Judge dataset builder 后续生成的 positive/claim template 原生写入 task type；工作台也强制在持久化 row 中补齐 task provenance。

真实 frozen 输出：positive 104 条均为 `task_type=evidence_relation`，claim 73 条均为 `task_type=claim_faithfulness`，均携带 contract version 和完整 allowed labels；当前 human label 为空，因此 target 为空并由 missing-label gate 阻断，`invalid_label_contract_count=0`。

### P34 Judge 请求级 Ledger 与精确续跑

正式 2×2 需要 initial Judge 加两次 fixed-packet repeat，旧实现一次 `generate_many` 中断会丢失整批结果并在重跑时重复消耗额度。新增 `scripts/p34_request_ledger.py`：

- 请求 key 冻结 title、prompt SHA256、stage、Judge code、group、packet、task、repeat 和完整 generation config。
- generation config 包含 provider/base URL/model/temperature/top_p/max_tokens/system prompt/JSON response mode。
- 只复用 `status=success` 且 key 完全一致的 raw response；prompt、model、repeat 或任一配置漂移都会产生新 key。
- API 请求按默认 8 条分批；每个成功批次立即原子写入 JSON ledger，后续批次失败不丢失已完成响应。
- 失败请求不写 success cache，续跑只重试缺失项。
- initial/final 每个 request 独立记录错误，不再因一个 batch 失败把整个 Judge group 都标成同一错误。
- Judge report 和 2×2 aggregate 显式报告 ledger path、cache hits、实际 API request 数和逐阶段统计。
- experiment lock 冻结 `checkpoint_batch_size=8` 和 `p34_request_ledger_v1` schema。

测试证明：首次 3 请求后重跑 3/3 cache hit、API=0；prompt/max_tokens 漂移 cache=0；第二批中断时首批与后续成功批保留，续跑只请求缺失 2 条。当前真实 preflight 因标签不完整而在 API 前阻断，ledger hits=0、API requests=0，ledger 文件未创建。

通用 API 生成器另修复了 `max_retries=0` 的零请求缺陷：现在该配置表示只尝试一次、不做重试，不能再生成“看似 API 失败、实际没有发请求”的假诊断。修复后进行 one-paper M/P 真实探针，`mimo-v2.5` 与 `mimo-v2.5-pro` 均执行请求并返回 HTTP 402 `insufficient_balance`；主/备用 key 切换逻辑已运行，但当前两者仍不可用。pipeline 状态为 `BLOCKED_DISCOVERY`，`active_changed=false`，canonical active 未被覆盖。

### P34 Frozen Label 一一对应完整性

旧 `_load_labels` 将多个 frozen 文件直接合并为 dict，同一 `packet_id` 会被后读文件静默覆盖，多余 label 也不会被识别。现新增 label-load diagnostics：

- 记录每个 label packet 的来源文件、总 row 数、unique packet 数和所有 duplicate rows。
- duplicate 即使内容完全相同也阻断；冲突重复额外记录 `identical=false`，但绝不覆盖首个来源。
- 2×2 preflight 要求 labels 与 combined packets 一一对应，任何 orphan label 均阻断。
- missing label、invalid contract、duplicate label、orphan label 分开报告，不能用总数相等掩盖 ID 集错误。
- 报告与 Markdown 显示 row/unique、duplicate 和 orphan 数量。

当前真实 preflight：177 packets、177 label rows、177 unique IDs、0 duplicate、0 orphan、177 missing human labels。结构完整性通过，但人工内容仍为空，因此继续在 API 前 BLOCKED。

页面验收：桌面端“刷新总闸”可真实触发统一刷新；390px viewport 无横向溢出，按钮稳定为 `82×34`，gate 摘要独占下一行，浏览器 console error 为 0。

当前完整聚焦回归：`1051 passed`。覆盖 ReviewState/Recovery/hygiene、field authority、PaperIndex/retrieval、完整人工编辑、PaperIndex 离线批量交换与 human-anchor gate、独立审核者认证与 Ed25519 提交完整性、标签交换包、reviewer 级 deterministic ZIP 和离线审核模板、symmetric discovery pipeline/activation、frozen annotation assignment、统一 label contract 与 cardinality、Judge request ledger/resume、API 零重试真实请求语义、2x2 完整四组仿真、统一 gate refresh、experiment lock、holdout bundle、人工标注与裁决链。

### P34 正式标注质量总览与最新模型健康探针

新增 `scripts/p34_annotation_quality_report.py`，并接入统一 gate refresh、annotation server、工作台 UI 与 experiment lock。该报告不改变标签或 ReviewState，只把正式标注执行中原先分散的信息收敛为一个可操作视图：

- 三类任务分别报告 primary/secondary 完成度、双标数量、raw agreement、Cohen kappa、分歧、待裁决和无效签名。
- PaperIndex 报告完成度、boundary/anchor recall、false-boundary rate 和签名完整性。
- 对称 discovery 独立报告 active packet 状态与最新 API health probe，不把余额失败误写成模型能力失败。
- 报告 reviewer role 注册状态、assignment 状态、2x2 missing label/invalid span，以及当前可以立即开展的工作流。
- 工作台新增只读 `/api/quality`，移动端进度区直接显示质量状态和关键阻塞；390px 实测 document/body width 均为 390，无横向溢出。

当前真实质量报告：

```text
P34_ANNOTATION_QUALITY_DASHBOARD_20260711.{json,md}
status = PARTIAL_ANNOTATION_READY
actionable_now = evidence primary/secondary + claim primary/secondary + PaperIndex primary
negative discovery = BLOCKED, packet_count=0
health_probe_error_codes = [insufficient_balance]
invalid_signature_count = 0
two_by_two_invalid_span_count = 0
```

最新正式 one-paper M/P health probe 已固化为：

```text
P34_2_SYMMETRIC_DISCOVERY_HEALTH_PROBE_20260711_*
P34_2_SYMMETRIC_DISCOVERY_HEALTH_PROBE_PIPELINE_20260711.{json,md}
```

MiMo `mimo-v2.5` 与 `mimo-v2.5-pro` 均真实请求并返回 HTTP 402 insufficient balance；pipeline 为 `BLOCKED_DISCOVERY`，raw candidate=0，`active_changed=false`。因此当前结论仍是供应商余额阻塞，不是 discovery/Judge 能力结论。

统一 gate refresh 仍诚实为 `BLOCKED`，但 draft experiment lock 已重建并验证 `PASS`、`mismatch_count=0`；精确 `config_sha256` 以 lock artifact 为准，避免在被锁定的计划文件内形成自引用漂移。工作台运行于 `http://127.0.0.1:8765`。

验证：本轮 P34 + ReviewState/Recovery/final-view hygiene 聚焦回归 `1042 passed`；质量总览、服务、gate refresh 和 lock 针对回归 `27 passed`。全仓 pytest 在收集训练/分布式测试时因当前环境缺少 `torch`、`ray`、`omegaconf`、`tensordict` 等依赖中止，不把它记为产品代码失败。

### P34 Reviewer 凭据恢复与轮换

独立 reviewer 身份门原先存在一个正式运营缺口：token 只在首次绑定时返回，服务端只保存 hash；浏览器存储丢失后，已绑定 reviewer 无法重新取得凭据，也不能安全改绑。现将 registry 升级为 `p34_annotator_registry_v3`：

- 首次绑定同时签发 256-bit token 与单次 recovery code；workspace 只保存二者 SHA-256，不保存明文。
- 浏览器只长期保存当前 token。recovery code 进入单独的 `p34_annotator_credential_v1` 本地凭据文件，不进入 localStorage、label、resolution、离线审核包、role ZIP、gate、lock 或论文 artifact。
- “导出凭据”必须先用当前 token 认证，然后原子轮换 token 与 recovery code；旧 token 和旧 recovery code 立即失效。
- “导入凭据”先验证 token；只有 token 已失效时才消费 recovery code。恢复成功后再次轮换并下载替代凭据，已消费 recovery code 不能重放。
- registry 记录单调递增 `credential_generation` 与 `recovery_count`，质量总览只暴露 registered/recovery-enabled/generation，不暴露 reviewer secret 或 hash。
- legacy v2 registry 可使用仍有效的当前 token 执行一次 authenticated rotation，升级到 v3；没有当前 token 且没有 recovery hash 时保持 fail-closed。
- `--allow-role-only-identity` 仅用于旧测试/迁移；verify/rotate/recover 在该模式中全部禁用，避免兼容开关绕过正式身份门。

安全测试证明：错误 recovery code 被拒绝；rotation 后旧 token 与旧 recovery code 均失效；recovery 后上一代 token 失效；registry 中不存在任一代明文 secret；不同角色仍不能复用 reviewer ID。工作台新增“导出凭据/导入凭据”，1280px 和 390px 均无横向溢出，浏览器 console error=0。

### P34 Experiment Lock 可达性与作用域 Git 策略

审计发现两个会使最终 holdout 永远不可达的问题：旧 lock 内部仍保存一套与 `P34_2_GATE_CONTRACT_20260711.json` 分叉的硬编码 thresholds；统一 gate refresh 虽生成 finalize manifest，却把未 finalized 的 draft manifest 交给 holdout。现完成结构性修正：

- `p34_experiment_lock_v2` 直接加载、校验并哈希冻结 gate contract；locked `thresholds.p34_2` 必须与 contract 内容完全一致，contract 修改、缺失或非法均由 `verify_lock` 检出。
- PaperIndex thresholds 保持独立命名空间，不再和 Judge capability threshold 混成一张可能漂移的表。
- Git clean policy 显式支持 `off|tracked|full`。正式 finalize 使用 `tracked`：只要求 experiment lock 的关键代码/计划/合同与 Git HEAD 一致；936 个全仓历史产物不再阻断，但任一关键文件未跟踪或修改仍 fail-closed。
- Git policy 是授权条件，不属于科学配置；draft=`off` 与 finalize=`tracked` 使用相同 datasets、split、代码 hash、readiness、model config 和 thresholds，因此 `config_sha256` 必须一致。
- gate refresh 的 holdout authorization 改为消费 `P34_EXPERIMENT_LOCK_FINALIZE_CHECK_20260711.json`。当 finalize 为 `FROZEN_READY` 时，同一 manifest 可直接授权 holdout；不再把 draft lock 送入一个必然失败的分支。
- 测试证明：无关未跟踪文件在 `tracked` policy 下不阻断；`full` policy 会阻断；关键代码修改立即产生 `git_tracked_scope_not_clean`；draft/final config hash 保持相同。

关键 P34 实现、合同、计划和专属测试已提交为 `8167031`。提交后正式 scoped Git audit 为 `tracked_dirty_entry_count=0`、`tracked_clean=true`，同时全仓仍有 890 个无关历史实验/工作区条目；后者不影响冻结。draft/final config hash 一致，draft verify `PASS`。finalize 当前只剩真实 readiness 阻塞：2×2、PaperIndex、positive/claim labels、symmetric discovery 和 annotation assignment；Git blocker 已归零。

### P34-2 真实对称 Discovery 恢复与严格激活

MiMo 主、副 key 更新后，one-paper 健康探测已真实通过。`mimo-v2.5` 与
`mimo-v2.5-pro` 均成功返回结构化 JSON；最初每篇上限 8 条时 Pro 在第 8 条中途触发
2048-token 截断，将上限收敛为 6 后得到 M=6、P=6、共 12 条有效候选，API error=0。

首次 hardneg20 运行暴露了一个 activation 语义缺陷：40 个 M/P 槽位中 39 个有效，
M 覆盖 19/20、P 覆盖 20/20，但旧 activation 只检查每个模型全局候选数大于零，错误地
报告 `ACTIVE_READY`。现已改为直接核验 `_CASES.json`：必须恰有 20 篇、40 个槽位，
且每篇 M/P 都有 `valid=true` 且 `candidate_count>0`；manifest coverage 还必须与 cases
计算值一致。19/20 fixture 和真实首次结果现在均 fail-closed。

使用每篇最多 5 条、max_tokens=2048 重跑 hardneg20 后，正式结果为：

```text
papers = 20
M valid coverage = 20/20, candidates = 100
P valid coverage = 20/20, candidates = 100
raw candidates / neutral packets = 200
issue types = 11
invalid span packets = 0
API errors = 0
activation = ACTIVE_READY
pipeline = READY_FOR_HUMAN_LABELS
```

11 类包括 missing_ablation、missing_baseline、insufficient_evaluation、
evaluation_protocol_risk、method_support_gap、result_claim_mismatch、scope_overclaim、
statistical_or_reporting_gap、reproducibility_gap、efficiency_cost_gap 和
missing_robustness_or_generalization。该数字是待人工审核的 discovery 候选数，不是
verified negative 数，不提前声称 precision 或 capability Go。

同时修复两项运行态审计问题：

- discovery 先热加载、assignment 后热加载，并强制运行态 review-issue secondary 数量
  等于冻结 assignment；当前为 20/20。
- gate refresh 不再把 Python 依赖崩溃的退出码 1 当成正常 BLOCKED 并读取旧 artifact；
  运行前移除旧报告，只有本次生成新报告才可继续，并允许显式选择具备 pandas 的 gate
  Python 环境。
- quality dashboard 不再把 `valid_case_count=40` 误当候选 packet 数；当前正确显示
  discovery packet_count=200、negative primary=0/200、secondary=0/20。

当前质量状态为 `READY_FOR_FULL_ANNOTATION`，可执行 evidence、claim、PaperIndex 和
review-issue 的 primary/secondary 标注。统一 gate 仍诚实为 `BLOCKED`：positive 0/104、
claim 0/73、negative 0/200、PaperIndex 0/20、2x2 missing labels 377。下一总闸是独立
人工金标准和裁决；其完成前仍不进入 P34-3B/3C 或 P34-4+ runtime 重构。

验证：新增严格 coverage、reload 顺序、陈旧 gate 和 packet-count 回归共 `11 passed`；
完整 P34 + ReviewState/Recovery/final-view hygiene 聚焦回归 `1055 passed in 7.12s`。

### P34 人工审核中文展示 Sidecar

为支持中文审核者复核，新增 `scripts/p34_translate_audit_paper.py` 与
`P34_AUDIT_TRANSLATIONS_ZH_20260711.json`。第一篇 hardneg20 论文 `ye3NrNrYOY`
的显示范围包括 5 条 evidence relation、3 条 claim faithfulness、10 条 review issue
和完整 PaperIndex 机器建议；去重后共 109 段、65,135 字符。MiMo-Pro 分批翻译后
109/109 有效，coverage=1.0，source scope SHA-256 为
`98b61bb6c721fc819a004ae7641d2023bac63c10278603168e9c169c3d7a13e6`。

翻译层只按英文字符串 SHA-256 注入 `display_translation`：

- 原始 packet、exact span、template、assignment、label contract、Judge prompt 和 gate
  输入保持英文且不变。
- label/anchor 保存仍写原始英文结构；中文只用于在线工作台阅读。
- 正向和 claim 标签显示中文名称，但提交值仍是冻结英文 code；A/B/C/D 显示中文简述，
  提交值仍是 A/B/C/D。
- 切换 evidence、claim、review issue 和 PaperIndex 时保留当前 paper 筛选，便于逐篇完整审核。

浏览器验收：第一篇论文四类页面分别显示 5、3、10、1 个筛选项；所有正文、审稿缺陷、
所需证据、反证问题、来源摘录与 PaperIndex 机器建议均显示中文。API 对照确认英文原始
claim 未改变，中文仅出现在 display sidecar；严格 discovery activation 仍为 PASS，M/P
覆盖保持 20/20。完整聚焦回归 `1059 passed in 7.25s`。
