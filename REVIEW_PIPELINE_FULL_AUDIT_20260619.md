# 审稿管线全环节审计(对齐"论文叙事")

- 日期:2026-06-19
- 审计者:Claude(独立复核 + 3 路子代理 + 逐条代码核实/复现)
- 代码基线:git HEAD `3b97956`(2026-06-15);**本批改动全部为未提交工作区状态**,下文标注 NEW=本批引入 / OLD=基线已有
- 北极星(论文叙事):**系统能产出"真实审稿发现的、论文可溯源的 verified negative",驱动诚实的 recovery 生命周期,且优化目标朝该行为对齐。** 审计即检验"实现是否真支撑这条叙事,在哪一环掉链子或造假"。

---

## 0. 一页结论

按"负向证据"在管线里的生命线 `产出 → 核验 → 计数/奖励 → recovery → 报告/指标` 逐环节看,叙事目前在**三个环节同时断裂**,且彼此叠加:

1. **产出环(P0,主因)**:Evidence Agent 合法 JSON 产出率 ~0–10%(最新 claimraw2 = **0/32,fallback 100%**)。叙事的原材料几乎到不了 verifier,所以 verified negative 全系列 ≈ 0,reward 反低于基线。
2. **核验环(P0,新引入回归)**:本批新建了三层负向语义门禁(净改进),但 `state.py:1100` 有一个**已复现的红线漏洞**——作者自陈局限被判成 `review_negative_verified`,且会**传导进 recovery**,现有 dashboard 守卫**看不见**。
3. **奖励环(P0)**:`reward.py:360` 读了一个**不存在的字段** `grounded_active_flaw_count` → 奖励里的 grounded-flaw 分量**恒为 0**。优化目标**结构上无法奖励**论文的核心命题,且"有据 reject"与"无据 reject"得分无差。

另有 baseline 漂移(P1)、claim salvage 残余风险(P1/P2)、若干流程/卫生问题(P2)。下面逐环节详列。

---

## 1. 产出环 — Evidence Agent JSON 可靠性(P0,主因)

| run | 真实证据轮 | json_valid | fallback | fallback 率 |
|---|---:|---:|---:|---:|
| claimraw2(最新) | 32 | **0** | 32 | **100%** |
| claimraw1 | 31 | 2 | 29 | 94% |
| semanticfix1 | 29 | 0 | 28 | 97% |
| diagpendingfix_default(0618) | 44 | 1 | 35+ | 80%+ |

- 直接元凶:**`max_tokens=768`**(claimraw2 log)对 5–7k 字符的证据 prompt 太低 → `truncated_*` + 截断致 `invalid_json`;叠加 **prompt 膨胀**(~9k 时失败 60%+,砍到 ~4.2k 的 targetguard 最低)。
- 后果:模型把 schema/prompt 原样复读(连 manager 都把占位符 `"Worker Agent Name"` 填进 `selected_agents`)。
- **对叙事**:HURTS(根部)。模型几乎不产出 grounded 负向,verifier 再好也无米下锅。详见同目录 `REALNEG_ROOTCAUSE_AUDIT_20260619.md`。
- 修复:max_tokens 768→1536(仍截则 2048);大幅精简 evidence prompt,把规则移进已有确定性 verifier;启用 JSON/受约束解码;**把 `evidence_json_fallback_rate` 设为 dashboard headline KPI,降到 <20% 前冻结一切下游负向调参**。

## 2. 核验环 — 三层负向门禁(P0,新引入回归)

**架构(NEW,净改进)**:`_is_grounded_paper_negative_evidence_record`(state.py:10260)= `_is_paper_negative_evidence_record` → (当 `_state_requires_verified_grounding` 为真,真实跑批恒真)→ `verified_grounding_label∈{exact,normalized}` + `semantic_grounding_label==semantic_negative_verified` + `_is_review_negative_verified_evidence_record`。被 11 处计数站点引用。基线(HEAD)**根本没有** `_assess_review_negative_relation` 等(HEAD=0 / 工作区=4),即旧线连这道门都没有——本批是红线净改进。

**已复现红线漏洞(P0,NEW)— `state.py:1100`**:`_assess_review_negative_relation` 中,TRUE_PAPER_NEGATIVE 类型只要命中很宽的 `concrete_gap` 正则即判 `review_negative_verified`,**未像 1102 行那样排除 author-limitation 措辞**。严格路径(有 quote bank)下复现:

```
quote = "A limitation is that we do not evaluate on the out-of-domain benchmark."
negative_evidence_type = "insufficient_evaluation"
→ _assess_review_negative_relation = review_negative_verified
→ _is_grounded_paper_negative_evidence_record = True   # 作者自陈局限被当成 verified negative
```

这就是用户红线"论文文字提取,而非审稿发现的缺陷"。三重放大:
- **传导进 recovery**:`recovery_validator._is_verified_negative_recovery_evidence` 对带 quote 的负向**强制要求 `review_negative_verified`**,所以 1100 误判会进一步触发 mark_contested/downgrade。
- **监测盲区**:dashboard `semantic_negative_without_review_relation_count==0` 守卫与新加的 `recovery_case_evidence_bucket_author_limitation_only` 桶**都抓不到**——漏点处 review 层自身误判为通过,样本进的是 `verified_review_negative` 桶。
- 修复(已验证有效):1100 的 concrete_gap 通道叠加 `not _REVIEW_NEGATIVE_AUTHOR_LIMITATION_RE.search(quote_l)`,或用 `source=Limitations`/self_anchor 区分"作者自陈 vs 审稿发现";补一条用该 concrete 措辞的回归测试;加一个能看见此类的计数器。

**次级(P2)**:语义底牌 `semantic_negative_verified`(`_assess_quote_semantic_grounding`,1574-1586)偏 lexical——只要含负向词 + 无数字/表格不一致即过,阈值低(0.08/0.14),判别力弱、放大上游误标后果。

## 3. 奖励环 — 优化目标无法奖励叙事(P0)

**`reward.py:360` 读取不存在的字段(已核实)**:`grounded_flaws = float(dh.get('grounded_active_flaw_count') or 0)`。hygiene view 全文**不产出** `grounded_active_flaw_count`(只产 `verified_actionable_negative_flaw_count`、`grounded_major_flaw_count` 等,state.py:6286-6539)。故:

- `flaw_density`(:367)恒为 0 → `0.15 * flaw_density`(:375)恒为 0 → **grounded 负向永不被奖励**;
- 决策分量权重为 0(:431),`reject` 是否正确不计分;
- 结果:8 篇全 reject、`es_flaw_density=0`,reward 仍 ~0.55–0.76,**"有据 reject"与"无据 reject"得分无差**。
- **对叙事**:HURTS(致命)。优化目标结构上不奖励"真实 verified negative",等于训练信号与论文命题脱钩。
- 修复:把 :360 指向真实存在的键(建议 `verified_actionable_negative_flaw_count`);给决策正确性合理权重;修复后旧 run 的 reward 不可直接比,需重新 baseline。

**positive 兜底掩盖崩溃(P1)**:grounding 第三档 `quote_bank_claim_overlap_canonical`(state.py:1892-1913)会在模型没逐字 copy 时,挑一条与 claim 重叠的 bank quote **替换**上去并判 paper_grounded。这让 positive support 在 JSON ~90% 失败时仍有量(`real_strong_support_total` 数十条),**把模型崩溃掩盖**,使 run 看起来比机制健康。负向侧无等价兜底(`quote_bank_salvage_generated_negative_count=0`,且 recovery 显式拒 `source=quote-bank-negative-grounding`),所以 negative 全裸暴露——这正是"positive 有量 / negative 恒 0"的结构成因。

## 4. claim 来源喂给负向(P1/P2)

- **门禁大体成立**:负向绑定在多处显式拦截 context/fallback/recovery claim id(state.py:2073-2093 `_is_real_paper_claim_id_for_negative`、10672-10677 `_is_paper_negative_evidence_record`、runner:368-398 `_is_negative_binding_claim_target`)。HELPS。
- **残余风险(MED,NEW)**:本批 raw-salvage 放宽了 meta 过滤(裸词 "user" 不再拒,只拒 "user asks/asked/..." 等显式短语;review_runner.py:5019-5023)+ 从截断 JSON 恢复**部分** claim 对象(claim_id+claim 完整即收)。而 `_should_canonicalize_raw_salvaged_claim`(state.py:617)一旦判定 canonicalize,就把 `claim-paper-fallback-*` **重切成 `claim-<text>` 真实 id** 并置 `paper_claim_canonicalized_from_raw_salvage=True`(state.py:644-646)——于是**被提升的 salvage claim 可以 host 负向**。
  - 注:子代理曾断言该 flag "从不置位",**经核实为误**(state.py:646 确实置 True;另见 manager_policy:697、runner:388/461 读取)。
  - 关键在 `_should_canonicalize_raw_salvaged_claim` 是否校验"claim 文本确实出自论文"。若宽松,则"放宽 meta 过滤 + 部分 JSON 恢复 + canonicalize 提升"三者叠加,可能把非真实 claim 提升为真实 claim 再挂负向。**建议重点复查这个函数**,并对 canonicalize 要求"claim 文本在 paper_text 中可定位"。

## 5. recovery 生命周期(大体 OK)

- mark_contested / flaw downgrade / claim downgrade / limitation routing **均要求 verified review-negative**(recovery_validator.py:405-447/809-828/911-920);带 quote 的负向必须 `review_negative_verified`(307-326)。HELPS。
- step1/2 正确落地:`record_diagnosis_pending_concern` 已移出 `recovery_effective_repair`(state.py:12116/12155),新增独立层 `diagnosis_pending_recorded`,并保留 `no_effect_commit` 的 `not diagnosis_pending_concern_added`(12129);记录路径由 `DRMAS_DIAGPENDING_RECOVERY`(默认关)gate + dedup(runner:95/3677/3707)。
- diagnosis_pending **无 verified-negative gate 属设计如此**(它本就是"待核验潜在 concern",源自确定性 `claim_requirement_audit`,非伪负向),且已隔离/默认关/不计 effective_repair。**唯一要求**:dashboard 不要把 `diagnosis_pending_recorded` 计入 recovery 成功口径(目前未发现,保持即可)。
- 提醒:由于 recovery 信任 `review_negative_verified`,**§2 的 1100 漏洞会传导到此**——再次说明 1100 优先级最高。

## 6. baseline 漂移 / A/B 纪律(P1)

- **prompts**:OFF 的 `CRITIQUE_PROMPT` 与 HEAD **不字节一致**——`_critique_prompt_baseline()` 用"从 hardneg 删字符串"重建,但 removal 那条 "True hard negatives..." 与 body 短句不匹配 → 删除静默失效泄漏;`negative_evidence_type` 枚举 5→13 也泄漏到默认线。根因是"删字符串重建 baseline"太脆。建议:保留字面 golden baseline 常量 + 加法构造 hardneg + 回归测试断言 OFF==golden。
- **manager_policy**:默认 `hard_negative_discovery_override` 的 else 不再设 `payload["focus"]`(baseline 的 "Search for copied paper quotes..." 已全删);`_negative_evidence_is_binding_candidate` 等的 negative_type 集合 ungated 扩张。
- **判定器本身 ungated、默认生效**:对正确性是好事,但意味着**默认 mainline 指标口径已变,旧 baseline 数字不再可比**。需拍板:作为新 mainline 重新 baseline,还是给它独立开关。

## 7. 监测盲区与流程卫生(P1/P2)

- **dashboard 盲区(P1)**:`semantic_negative_without_review_relation_count==0` 与 `recovery_case_evidence_bucket_author_limitation_only` 都**抓不到 1100 漏点**(见 §2)。建议加"concrete_gap 通道命中 author-limitation 措辞却判 verified"的专项计数。
- **CLAIMRAW 的'胜利样本'是反面教材(P1)**:计划里 QA 的目标负向 `"Note that we do not evaluate the quality of the output..."` 本身是作者自陈局限,正撞 1100 漏点。**必须先修 1100,再验证 targeted-search**,否则 targeted-search 越好用,越高效地批量生产假负向。
- **CLAIMRAW2 是废跑(P2)**:启动未带 `DRMAS_TARGETED_NEGATIVE_SEARCH=1`,八篇 `targeted_negative_search_required=false`,没测到目标路径。建议把"turn log 里断言 flag 真生效"写进验收前置。
- **大批未提交(P2)**:verifier+runner+policy+prompts+dashboard 全堆在 06-15 HEAD 之上未 commit。建议先归一个分支/快照再动手,避免状态丢失。
- **死代码(P2)**:state.py:115-120 在 `_normalize_conflict_note_text` 的 return 之后留了一段不可达代码(误粘 `_normalize_text` 体),清理即可。
- py_compile 六个核心文件通过。

---

## 8. 修复优先级(建议执行顺序)

**P0(先做,且按此序)**
1. **Evidence JSON 可靠性**:抬 max_tokens(768→1536/2048)+ 砍 evidence prompt + JSON health KPI;降到 <20% 前**冻结下游负向调参**。这是唯一应先做的事——否则任何 A/B 都被 ~90% 噪声埋掉。
2. **修 `state.py:1100`** author-limitation 短路漏点 + 回归测试 + 可见性计数器。**排在 targeted-search 验证之前。**
3. **修 `reward.py:360`** 死字段,指向真实 grounded-negative 键;决策正确性给权重;修后重新 baseline。

**P1**
4. baseline 漂移:prompt golden 重构 + 断言 OFF==golden;恢复/确认 manager_policy 默认 focus;判定器是否新 mainline 一并拍板并重新 baseline。
5. 复查 `_should_canonicalize_raw_salvaged_claim`,要求 canonicalize 时 claim 文本可在 paper_text 定位;收紧 raw-salvage meta 过滤。
6. dashboard 加 1100 盲区专项计数。

**P2**
7. 未提交批次先归分支;targeted-search 加 flag-生效断言;清死代码;targeted-search 验收加"非作者自陈局限"门。

---

## 附:本批 step1/2/3 落地状态(供对照)

- step1(diagnosis_pending 移出 effective_repair)= 已正确实现(含 no_effect 陷阱)。
- step2(记录路径独立 flag `DRMAS_DIAGPENDING_RECOVERY`,默认关)= 已实现。
- step3(给 diagnosis 一等调度入口)= **未进默认线**;hardneg-diagnosis / targeted-search / compact-pass 三条全为默认关 gated 实验,其中 targeted-search 是 P-B 正解(Evidence 形成 grounded 负向或 not_assessable)。
