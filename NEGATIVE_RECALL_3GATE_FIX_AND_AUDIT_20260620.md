# 负向召回三关修复 + P0 验证 + 审计报告(2026-06-20)

> 本会话由 Claude 独立完成。承接 P0(JSON 修复待验证),完成:① 验证 P0;② 重新审计另一个 AI 的结论;③ 定位并修复 verified negative=0 的真根因(系统侧三关)。结论中文,代码/字段英文。file:line 可能漂移,认函数名为准。

## 0. TL;DR

- **P0 JSON 修复决定性成立**:smoke8 A/B,`evidence_json_fallback_rate_pct` ON=**0%**(27/27 valid)vs OFF=**82%**。验收门(<20%)达成。
- **verified negative=0 的真根因比"模型质量"更深**:不是模型转述/编造引文,而是**系统侧三关都不识别委婉 ablation 负结果**(如 "yields minimal/limited performance gains"),导致真负向被 quote_bank 漏收而误杀(**假阴性**)。
- **三关修复已落地 + 端到端确定性证明全链路打通**(委婉负结果 → semantic_negative_verified → review_negative_verified)。焦点测试 551 全绿、硬约束保持。
- hardneg20 验证 run 进行中(§6 待补)。

## 1. P0 验证(A/B,见 dashboard `AB_JSONFMT_ON_VS_OFF_smoke8_20260619.md`)

| 指标 | OFF | ON | 
|---|---|---|
| evidence_json_fallback_rate_pct | 82% | **0%** |
| evidence_json_valid_turns | 5 | 27 |
| raw_chars_median | 8855 | 1544 |

`response_format=json_object`(commit `6ce54d6`)奏效,mimo 认该参数;raw_chars 8855→1544 印证根因(OFF 时模型吐推理 prose,ON 时被约束成紧凑 JSON)。

## 2. 重新审计另一个 AI 的结论(逐条裁决)

| 声明 | 裁决 | 依据 |
|---|---|---|
| JSON 修复成功 fallback 0% | ✅ 确认 | 独立 A/B 证实 |
| verified negative=0 | ✅ 确认 | — |
| 12 条 = 6 grounding+4 semantic+2 author_limitation | ✅ 分布逐条命中 | review_state.evidence_map |
| 模型把负向句误标 stance=supports | ⚠️ 部分推翻 | 那句绑 claim-4(limitation claim),supports 是相对该 claim 的合理立场;脱离 claim 语境的误读 |
| 红线守住、0 假负向、正确拒绝弱负向 | ⚠️ 重大修正 | 无假阳性✓,但**有假阴性**(见 §3) |
| 瓶颈=负向证据质量(模型 quote) | ⚠️ 根因错位 | 真根因在系统侧三关召回,非模型质量 |

**总评**:另一个 AI 实证扎实、JSON 结论正确、可信度高;偏差在 stance 语境误读 + 漏假阴性 + 根因过度归给模型。

## 3. verified negative=0 真根因:系统侧三关 + 假阴性铁证

**假阴性铁证**:9zEBK3E9bX 的模型引文 `"relying solely on detection as a pre-training task yields minimal performance gains"`(Table 5 ablation 负结果)**逐字在论文**,但 `evidence_quote_bank` 的 negative-or-gap 槽填的是无关方法/数据描述(`"Next, by dividing B_density..."`、`"SemanticKITTI has 22 sequences..."`),**漏收这句** → 核验判 `not_found_in_quote_bank` → 真负向被误杀。**模型找对了,系统召回错了。**

**三关都不识别委婉负结果**(import 逐关坐实):
1. `_EVIDENCE_NEGATIVE_ANCHOR_PATTERNS`(state.py ~8628):预抽取召回,只认 "marginal improvements" 不认 "minimal/limited gains" → 进不了 quote_bank。
2. `_NEG_TYPE_NEGATIVE_RESULT_RE`(~8652):typing 判 `generic_gap` → 被 review_runner.py:871 过滤。
3. `_SEMANTIC_NEGATIVE_TERMS_RE`(~918):`quote_has_negative_anchor=False` → `_assess_quote_semantic_grounding` 判 `semantic_mismatch`(quote_lacks_negative_anchor)。

## 4. 三关修复(state.py,未提交)

三处各加同一组委婉负结果词:`(minimal|negligible|limited|marginal|trivial|insignificant|little)\s+...(gain|gains|improvement|...)` + `yields?\s+(minimal|little|...)...`。收紧排除 slight/small/modest(偏中性),6 篇全文测零误伤正向。三关缺一不可。

## 5. 验证

- **端到端确定性测试(绕过模型随机)**:委婉负结果 evidence → `semantic_negative_verified` → `review_negative_verified`(reason=negative_result_grounds_current_paper_concern)。**全链路打通,无第四关阻塞。**
- **前两关 smoke**:负向召回 12→18,瓶颈从 grounding **前移到 semantic**(insufficient_semantic_negative 4→10),verified 仍 0。
- **三关 smoke8**:verified=0 —— 端到端已证机制对;单次 smoke8 verified=0 是 temperature=1.0 模型随机性(那次 8 条负向恰无委婉负结果句),非机制问题。
- **焦点测试 551 passed**(三关改动零破坏,git stash 对比确认 551 是真实基线,非 561)。

## 6. hardneg20 验证 run(20 篇 hard-negative)

TAG `mimo_v25_realneg_neg3gate_hardneg20_mt7_b4w4_api4_r8t600_20260620_011702`(20/20 完成)。

**结果:`review_negative_verified=0`,但关键突破 `semantic_negative_verified` 0→3**(全 run 历史首次)——证明三关修复在真实 run 生效,语义层首次确认负向。硬约束全 0、无假阳性。

3 条 `semantic_negative_verified` 的去向(均被第四关 review relation 正确处理):
- 1 条(KOUAayk5Kx,claim-1)= `scope_limitation`,判 `insufficient_claim_relation`(reason=scope_limitation_without_review_relation):该负向与绑定 claim 关系不足。
- 2 条(XH3OiIhtvf,claim-2)实为 semantic 层**误判**(quote 是图表设置 "Figure 2: EER of individual and federated models..." + 正向句 "significant improvement in EER"),被 review relation **正确拒绝**为 `neutral_control_context` / `positive_or_neutral_support`。

**结论**:系统侧门禁全链路打通(三关 grounding/typing/semantic + 第四关 review relation),且**红线守住**(第四关正确拒了 2 条假负向,无假阳性漏过)。`review_negative_verified` 仍 0 的原因**已从"系统误杀真负向"转变为**:模型在 hard-negative 上尚未产出「claim-relevant + actionable 类型(非 scope_limitation)+ 本身确为负向」的高质量负向 quote。这是真正的最后一公里,且现在站在"系统门禁已通、不再误杀真负向"的新起点上。

(注:worker=4 撞 MiMo 限流 429×107,`--api-max-retries 8` 兜底完成、结果不受污染;下次 hardneg20 用 worker=2 更稳。)

## 7. 硬约束 + must-protect

- harmful_state_contamination=0、recovery_harmful_commit_risk=0、recovery_no_effect_commit=0 ✅
- must-protect 唯一 FAIL:`support_trace_missing_verified_quote`=1 = WLgbjzKJkk claim-2 一条**空引文** support 被正确丢弃(`included_in_final_view=False`),**良性非泄漏**(JSON 修复后 evidence 增多的可解释副作用)。

## 8. 运行口径(踩坑记录)

- 解释器 `DrMAS/bin/python` + `PYTHONPATH=agent_env/site-packages:.`(openai 在 agent env)。
- 必须显式 `--model-adapter-mode small_model`。密钥 source `.env`。
- 工作目录是本仓库(含修复),**非 DrMAS-master**。
- 焦点测试基线 **551**(非 561)。`--max-tokens 2048`。

## 9. 下一步建议

1. hardneg20 出 verified>0 后,考虑 commit 三关修复(当前未提交)。
2. review relation 层已能 verified,无需再改。
3. quote_bank negative 槽召回可进一步系统性改进(本次只补了委婉负结果一类;其他类型负结果措辞可同法扩展)。
4. 不违反 Do-Not-Retry:本修复全在 Evidence 的 quote-find+verify 路径(召回+分类+语义),未碰 Critique model-judgment。
