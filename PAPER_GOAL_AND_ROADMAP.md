# 论文目标、系统目标与开发路线图（PAPER_GOAL_AND_ROADMAP.md）

最后更新：2026-06-14。本文件是 P26 阶段的**纲领文件**：它把"论文要讲什么"→"系统要实现什么"→"当前差在哪"→"下一步怎么走"串成一条线，作为后续开发/审计的总护栏。
配套：开关说明见 [`SWITCHES.md`](SWITCHES.md)，压制点代码定位见 [`P26_NEGATIVE_DISCOVERY_CODE_LOCATIONS.md`](P26_NEGATIVE_DISCOVERY_CODE_LOCATIONS.md)，决策日志见 [`memory.md`](memory.md)。

---

## 0. 一句话定位

本项目服务于一篇论文。论文讲的不是"更会写审稿意见的 LLM"、不是 accept/reject 判别器、也不是单纯证据检索，而是：

> **构建一个面向 LLM 辅助论文审稿的、结构化 / 证据对齐 / 可审计 / 可恢复的 ReviewState 管理框架**，让审稿从"输入论文 → 直接生成 review"转变为"输入论文 → 构建并维护 ReviewState（claim/evidence/flaw/gap/concern/conflict/recovery）→ 生成受控的 final review"。

四个贡献关键词：**structured / evidence-grounded / auditable / recoverable（结构化 / 证据对齐 / 可审计 / 可恢复）**。最终的 accept/reject 只是健康检查，不是主张。

---

## 1. 系统实现目标（8 项）与当前状态

| # | 系统目标 | 状态 | 依据（hardneg20 实测） |
|---|---|---|---|
| 1 | 结构化 ReviewState（claim/evidence/flaw/gap/concern/contested/recovery/audit 全部带 ID 可追踪） | ✅ 较成熟 | schema 完整，turn log + state snapshot 可审计 |
| 2 | 正向证据真实、可定位、可追踪 | ✅ 较成熟 | qhyg: real_strong=102, empirical=82, papers_with_real_strong=20/20, zero_real_papers=0, support_trace_missing_verified_quote=0 |
| 3 | 负向证据从"噪声"变"审稿问题"（过滤章节头/引用/future-work/自夸） | 🟡 初步有效 | option B(qhyg) 把 grounded 负向噪声占比 54%→~17%（7→2），且不破 recovery 红线 |
| 4 | 负向证据转化为 review-oriented concern（类型多样、actionable 充分） | ❌ **核心短板** | 最好一组 actionable=8 / potential=8（目标 ≥12 / ≥10）；missing_ablation/insufficient_evaluation/reproducibility_gap/result_claim_mismatch 长期=0 |
| 5 | 保留证据冲突（contested relation）而非粗暴覆盖 | ✅ 较稳定 | qhyg: contested_effective=7, mark_contested=7, negative_verified_target_preserved=15, open_conflict=0 |
| 6 | Recovery 安全、可验证、不伤状态 | 🟡 安全但单一 | recovery_no_effect_commit=0, harmful_risk=0, effective_repair=7；但 operation 几乎只有 mark_contested |
| 7 | Gap lifecycle 闭环（stale gap 清理） | ❌ 不稳定 | qhyg open_gap=0，但 reclass/默认基线 open_gap=6；resolve_stale_gap 触发=0 |
| 8 | 机制结论经 repeated-run 验证（非单次方差） | ❌ 未做 | 当前结论多来自单次 temp=1.0 run |

---

## 2. 当前指标快照（三组单次 hardneg20，mt7，仅供定性参考）

> ⚠️ 单次 temp=1.0 run，组间差异**大部分是采样方差**，不能直接当机制因果。

| 指标 | negaggr(仅7.3) | 默认/reclass(=guard3默认*) | qhyg(option B) |
|---|---|---|---|
| real_strong_support_total | 104 | 92 | 102 |
| empirical_real_strong | 89 | 71 | 82 |
| zero_real_papers | 0 | 0 | 0 |
| negative_evidence_candidate | 17 | 15 | 13 |
| verified_actionable_negative_flaw | 7 | 8 | 6 |
| potential_concern | 7 | 8 | 6 |
| missing_ablation / insufficient_eval / reproducibility / result_mismatch | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 |
| scope_overclaim | 0 | 7 | 0 |
| scope_limitation | 19 | 16 | 14 |
| recovery_effective_repair | 5 | 7 | 7 |
| recovery_no_effect_commit | 1 | 0 | 0 |
| mark_contested_commit | 5 | 7 | 7 |
| contested_relation_effective | 5 | 7 | 7 |
| evidence_gap_open_count | 0 | 6 | 0 |
| state_contamination_count | 0 | 0 | 0 |

\* reclass 那次 7.5 触发 0 次，等价于 guard3 默认基线。

---

## 3. 三个确定性结论（不受 run 方差干扰，已用隔离实验验证）

1. **7.5（DRMAS_NEG_RECLASSIFY）当前空转**：在 hardneg20 上触发 0 次（`negative_type_reclassified_from` 计数=0；同 jsonl 开/关该开关 dashboard 完全相同）。原因：系统抽出的 claim 是**描述性**的（"the method uses X"），不带 overclaim 语言，broad-claim 条件命中率为 0。→ reclass run 的任何改善**不能**归因于 7.5。
2. **7.3（DRMAS_NEG_DISCOVERY_MODE=aggressive）净负**：多发现的负向几乎全进 scope_limitation 噪声，且啃掉 mt7 轮数预算（evidence 轮 95→108，多的全是 question-only）→ recovery 退化（effective_repair 5、no_effect 1、mark_contested 5）。
3. **option B（DRMAS_NEG_QUOTE_HYGIENE）是唯一确定性正向**：减噪 54%→~17%，不破任何红线。但它只解决**质量**，不解决**覆盖/数量**。

**额外验证（2026-06-14）**：缺失类型（missing_ablation/insufficient_evaluation/reproducibility_gap/result_claim_mismatch=0）**不是分类问题**——扫描两个 run 全部负向证据，"内容像缺失类型却被标成别类"的真实句子≈0（少数"命中"是表格标题如"Table 5: Ablation study…"，说明论文**有**消融而非缺）。结论：**这些类型的内容根本没被 surfacing 进来，是 discovery/retrieval 问题，不是 classification 问题。**

---

## 4. 当前不足（9 项，含诚实归因）

1. **负向证据覆盖不足**：candidate 13–17（目标≥18），actionable 6–8（目标≥12），potential 6–8（目标≥10）。无一组达标。
2. **负向类型覆盖严重不足**：missing_ablation/insufficient_evaluation/reproducibility_gap/result_claim_mismatch 长期=0。**已验证是 discovery/retrieval 问题，非分类问题。**
3. **qhyg 只解决质量不解决覆盖**：定位为 negative-evidence **quality module**，不是 recall module。
4. **7.5 空转**：机制已实现但当前数据不触发；真正前置任务是 **claim extraction/typing**（让系统抽出 abstract/conclusion 里的 broad/SOTA/generalization 主张），不是继续调 reclass 正则。
5. **7.3 净负**：naive recall expansion 伤 recovery；只能在 qhyg + budget guard 保护下、改成 quality-aware 后重试。
6. **Recovery operation 单一**：几乎只有 mark_contested；resolve_stale_gap（**代码已存在，dashboard 有计数器，当前=0，只差触发条件**）、route_to_assessment_limitation、rebind_evidence 等未打通。
7. **Gap lifecycle 不稳定**：open_gap 在 0 和 6 之间漂（受运行轨迹/方差影响）；目标是所有主线配置稳定 open_gap=0 且 resolve_stale_gap≥1。
8. **缺 repeated-run 稳健性**：decision(14/6,10/10,15/5)、scope_overclaim(0/7)、candidate(13/15/17)、gap_open(0/6) 都在单次方差内，不能当机制证据。
9. **最新主线未在 full39 验证**：qhyg/type-targeted 之后还没跑 full39。

**已较成熟**（可写进论文雏形）：ReviewState 结构化、正向证据 grounding、final-view hygiene、state contamination 防护、负向 quote 初步减噪、contested relation、mark_contested recovery、recovery harmful/no-effect 防护。

---

## 5. 下一步计划（分阶段，每步都要守红线 + 多次验证）

> 主线从 **reclass-driven** 修正为 **quote-quality-first + type-targeted negative discovery**。

### P0 — 稳定 option B（唯一确定性正向），并确立多次验证纪律
- **P0.1 补 qhyg 两处残留噪声正则**：① 裸引用标题（无作者列表，如 "…: Current limitations and effective designs."）；② future-plan 方向句（"we will / we plan to / we intend to" + focus/investigate/explore，且无真负向 cue）。**必须保留**任何含真负向 cue 的句子（fails/cannot/does not generalize/limited to/without ablation/not evaluated/underperforms/drops/weaker/insufficient）。补单测。
- **P0.2 qhyg 稳健性验证**：`default × 3` vs `qhyg × 3`（其余参数一致：hardneg20 / mt7 / b4w2 / mimo-v2.5 / temp1.0 / mt768）。每次产出 dashboard + case audit + **noise audit**（统计 grounded_negative_total / 各类 noise count / true_negative / noise_rate）。
- **P0 验收**：noise_rate ≤20%；recovery_no_effect_commit=0、harmful_risk=0、contamination=0、unlinked=0、open_conflict=0；effective_repair / mark_contested / actionable / potential **不低于 default 均值 −1**。若减噪明显但 actionable 比 default 低 >2 → 说明误杀真负向，需收紧过滤。

### P1 — 类型定向负向发现（主战场）+ 先验诊断
- **P1.0（先做，便宜）context-coverage 诊断**：核查缺失类型的论文段落（ablation 表 / 评估设置 / 复现细节）**到底有没有进入喂给 agent 的 evidence context**。回答"是没喂进来（→改 section selection）还是喂了没发现（→改 prompt）"。这一步避免重蹈历史上 `Critique Context Selection v1/v1.1` 的覆辙（那次更激进地 prompt 找负向，结果 fallback/meta flaw 变多、净负、被回滚）。
- **P1.1 type-targeted discovery**：让 Critique/Evidence Agent 按**类型槽位**找负向（missing_ablation / insufficient_evaluation / reproducibility_gap / result_claim_mismatch / missing_baseline / scope_overclaim / negative_result），每槽返回 found/not_found + raw_quote + locator + bound_claim_id + why_this_type + confidence。
- **P1.2 type-targeted quote bank**：负向 bank 按类型分槽，每类最多 1–2 条，每篇进 critique 的负向 quote 上限 4（避免 7.3 那种"多但全是噪声"）。
- **关键护栏（我的补充，务必遵守）**：
  - **类型数量目标必须是"机会条件型"**——只在论文确实有该弱点时才期待该类型。`not_found` 是**完全合格的正常输出**，不是失败。**严禁**为凑指标硬造（撞红线"不为数量牺牲 grounding"）。
  - **semantic verifier 是硬闸**：type-targeted 只负责"提名候选"，最终是否计入由既有 verifier 决定。
  - 带着"**可能 no-go**"的先验做，单跑看信号再决定是否 3×。
- **P1 验收（机会条件下）**：actionable≥12、potential≥10、candidate≥18、unlinked=0、semantic_anchor_conflict=0；类型上至少新增 missing_ablation/insufficient_evaluation/reproducibility_gap/result_claim_mismatch 中的 **2 类 ≥1**。达不到则回到 P1.0 的 section selection。

### P2 — quality-aware aggressive（重试 7.3）+ recovery operation 扩展
- **P2.1 7.3 重试**：仅在 qhyg 稳定后，跑 `aggressive + qhyg`（暂不加 7.5）。给 7.3 加 **budget/quality guard**：剩余轮数<2 不再 discovery；question_only 连增则停；已有≥2 verified actionable 则转 recovery；当前候选全是 qhyg-noise 则停。即从 count-aware 改成 **quality-aware**。验收：candidate≥18 且 actionable≥12 **同时** recovery_effective_repair≥7、no_effect=0、question_only 不显著高于 default、gap_open=0。候选升但 recovery 降 = 失败。
- **P2.2 打通 resolve_stale_gap**（已存在，接触发条件）：gap open 且同 claim 后续已有 verified strong support / 被 verified evidence superseded / final view 已是 supported|contested → resolve。禁止：删真实 unresolved、删 assessment limitation、删 linked negative、"没找到证据就标 resolved"。验收：resolve_stale_gap_turns≥1、open_gap=0、no_effect=0、harmful=0。

### P3 — repeated-run 稳健性（贯穿，不是单独靠后阶段）
- 每个关键配置 ≥3 次重复跑，报 mean/std/min/max/best/worst。
- **采用规则**：安全红线全 0 + 均值改善 + **worst-case 不破红线** + 不是单次 best 才好 + 负向提升非靠噪声堆 + recovery 不退化。
- 优先级：先把**便宜且确定**的（qhyg vs default）做 3×；探索性的（type-targeted）先单跑出信号再 3×，省额度。

### P4 — full39 验证（最后）
- 前置：hardneg20 上 qhyg 稳定减噪、type 覆盖至少新增 2–3 类、actionable≥12、potential≥10、no_effect=0、harmful=0、open_gap=0、contamination=0。
- full39 目标：protection PASS、红线全 0、real_strong≥180、empirical≥120、zero_real=0、candidate≥20、actionable≥12、potential≥12、contested_effective≥10、mark_contested≥10、resolve_stale_gap≥1。

---

## 6. 未来规划（更长视野）

1. **救活 7.5（claim-and-context-aware）**：前置是 claim extraction 能抽出 abstract/conclusion/title 里的 broad/SOTA/generalization/robustness 主张。届时 7.5 从 `claim_aware` 升级为 `claim_and_context_aware`（看 claim 来源 section、邻近正向支持、作者声明的 scope），把"broad claim + narrow evidence"识别为 scope_overclaim。属 P2/P3 之后。
2. **更丰富的 recovery family**：在 resolve_stale_gap 稳定后，谨慎评估 route_to_assessment_limitation、rebind_evidence、convert_negative_to_gap。**claim downgrade（downgrade_final_to_candidate / downgrade_claim_to_unsupported）在 negative type coverage 稳定前一律不开。**
3. **论文实验呈现**：从 case-level diagnostic 升级为 repeated-run 的稳健统计表（mean±std + worst-case 安全）；主表围绕四关键词组织。
4. **section/retrieval 层**：若 P1.0 诊断指向"没喂进来"，则把论文段落选择（ablation/eval/repro 段）做成 type-aware retrieval，这可能是比任何 prompt 改动都更根本的杠杆。

---

## 7. 命名与方法论纪律

- 当前阶段**不要**命名为 `reclass success` / `negative quantity success` / `final baseline`。
- 当前准确命名：**`NEGATIVE_QUOTE_HYGIENE_DIAGNOSTIC_STAGE`（负向证据清噪诊断阶段）**——是"清噪阶段"，不是"覆盖完成阶段"。
- 任何"机制有效"的结论必须有 repeated-run 支撑；单次 best run 不作数。

## 8. 不可逾越的红线（任何改动都不能破）

```
final_nonreal_strong_support = 0
low_score_promoted_strong = 0
final_report_leakage_paper_count = 0
user_report_leakage_paper_count = 0
synthetic_marker_in_supporting_count = 0
negative_evidence_unlinked_to_flaw = 0
state_contamination_count = 0
harmful_state_contamination_count = 0
contamination_evidence_misbinding = 0
contamination_harmful_recovery_risk = 0
negative_semantic_anchor_conflict_count = 0
open_conflict_count = 0
recovery_no_effect_commit = 0
recovery_harmful_commit_risk = 0
```
并且：不放开 claim downgrade；不让 quote-bank negative 直接降级 claim；不把 generic gap 包装成 negative；不让 fallback/context claim 成为 claim-status patch target；不强推 grounded_weakness；不为数量牺牲 semantic grounding。

## 9. 叙事重定位：缺陷定位 = claim-evidence 推理为主，负向 quote 为佐证（2026-06-15）

### 9.1 核心重定位

之前把"负向证据收集"理解成**从论文文本抽取负面句子（worse/fails/missing/limited）**。审稿后认定：**这条路径不适合作为缺陷定位的主叙事。**

原因：抽取负面句子本质是"作者自陈 limitation 的收集器"——它只能找到**论文文本里出现负面词**的弱点（作者承认的局限、报告的负面结果），而**系统性地漏掉审稿中最有价值的那类批评：作者未言明的缺陷**（没做的 baseline、相对证据的 overclaim、方法支撑不了结论、评估不充分）。这些缺陷论文文本里不会出现负面词。若以此为主叙事，等于把"关键词/情感抽取"包装成"审稿"，是论文最易被攻击点。经验预测：用人类 gold review 评估时，文本抽取法会系统性匹配不上（人类批评多为未言明缺陷）。

**重定位后的贡献叙事**（对齐四关键词 structured / evidence-grounded / auditable / recoverable）：

- **缺陷定位的主机制 = claim-evidence 对齐推理**：追踪 claim、绑定证据，定位 (a) **claim-requirement gap**（claim 缺它该有的证据类型，是推理出来的、不依赖论文承认）、(b) **contested relation**（正向支持 vs 负向证据冲突）、(c) **recovery**（早期判断可被结构化 patch 修正）。
- **负向 quote 提取 = 佐证 / evidence 层，从属地位**：一条好批评 = claim-evidence gap（推理）+ paper-grounded quote（佐证）。负面句子用于**支撑**一个 flaw 的 grounding，不是 flaw 的来源。
- **重读 option B 的价值**：它不仅是"减噪"，更是**挡住系统把抽到的负面句直接当 flaw** 的护栏——防止退化成关键词审稿。

### 9.2 机制再平衡原则：**降单价，不降优先级**——每个环节都保证跑到

**纠正一个早期误解**：再平衡的目标**不是**把负向检测降级为"可跳过/best-effort"的二等环节（那会让它"没那么重要"，不是我们要的）。目标是：**整个流程的每个环节（claim → 证据/支持 → 负向检测 → contested → recovery → report）都保证在每篇论文上执行、一个都不少**，但让负向这一环**更省轮次（降单价）**，从而不挤压其它环节。

关键观察：**claim-requirement gap 与 contested 检测是 view 级审计，几乎零轮次成本**；它们要的是良好的 claim 覆盖 + 每个 claim 的证据被充分绑定。而负向检测现在是**分散在 5–6 个各自吃一轮的 override**（hard_negative_discovery / negative_formation / binding_retry×2 / recheck / challenge）——一多就吃光稀缺的 mt7 轮次，正是 7.3-aggressive 挤垮 recovery 的根因。所以问题不是"负向该不该做"，而是"负向做得太散太贵"。

预算优先级（每个环节都保证执行）：

```
claim 抽取 → 每个真实 claim 的证据验证/绑定（正向支持 + 覆盖）
           → (近乎免费) claim-requirement gap 审计 + contested 检测
           → 负向检测：保证执行的环节，但合并增效(见 9.3 P-A)，只占少量轮次
           → recovery
           → report
（best-effort 的只是"额外去找佐证 quote"，不是负向检测本身）
```

### 9.3 具体调整（分阶段、mode-gated、多种子验证后才并主线）

- **P-A 负向检测"合并增效"（核心，修正版）**：**不是**让负向变 late/可跳过，而是把现在分散的 5–6 个各吃一轮的 override（discovery / formation / binding_retry×2 / recheck / challenge）**合并成一次 gap 引导的高效负向 pass**，且尽量在 Critique/Evidence Agent **本来就会跑的那一轮内**完成（用 view 级的 claim-requirement gaps 当"该查哪些 claim/哪些类型"的指路牌），而不是 manager 为每个负向子任务分别 routing 一轮。效果：负向检测**仍是每篇必跑的环节**，但轮次成本从 ~3–4 降到 ~1，释放的预算保证 claim 覆盖 / recovery 不被挤掉。**这是把"散而贵"改成"准而省"，不是把负向变次要。**
- **P-B 用 gap 重排序"已有的" verify_evidence 轮次（安全版 targeted）**：claimreq audit 保持 view 级零轮次；用其 gap 结果去**重排序系统本来就会花的 evidence 验证轮次的 target 选择**（优先验证有 requirement gap 的真实 claim），**不新增搜寻轮次、不把 gap 作为 live prompt 指令**（后者已证明会诱导 question-only、压低 support，严禁重蹈）。
- **P-C 负向 quote 降为佐证**：形成 claim-evidence gap / contested 时，若 quote bank 里**现成**有 paper-grounded 负向 quote 就附上作 grounding，**不为它花专门的 hunt 轮次**。（注意：这里 best-effort 的是"额外找 quote"，负向检测环节本身仍保证执行。）
- **保留约束（重要）**：contested relation **需要**负向证据来"争议"正向支持，所以负向线**不能清零也不能变可选**——它是保证执行的环节，只是更省。

### 9.4 验收与纪律

- 目标：在守住第 8 节全部红线的前提下，**释放的轮次让 claim 覆盖 / 每 claim 证据绑定上升**（如 claims_with_2plus_independent_support、primary_claims_with_deep_support），claim-requirement gap 与 contested 因输入更全而更可信；recovery 不退化。
- 必须**多种子**（≥3）验证：均值改善 + worst-case 不破红线 + 不靠单次 best run。
- **不重蹈覆辙**：不恢复 7.3-aggressive；不把 claimreq 接回 live prompt；不做全局 fallback/support 抑制；负向重排序只动 target 选择，不动 claim status。

### 9.5 诚实的 limitation（论文里要写实）

系统对"作者自陈负向 / claim-evidence gap / 正负冲突"做得**精准**（高精度、可审计、可恢复），但**未言明的深层缺陷**（需要更强推理 / 领域知识 / 跨段落综合）仍是开放难题，且受小模型 + mt7 预算限制。这是核心 future work，不藏。
