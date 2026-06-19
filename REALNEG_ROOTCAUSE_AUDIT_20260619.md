# realneg 系列"verified negative 恒 0"根因审计

- 日期:2026-06-19
- 范围:0619 `realneg_*` 系列 smoke8 跑批(semanticfix1 / quotetask1 / claimgate1 / quoteactive1 / claimraw1 / claimraw2 / sidechannel{,2,3} / recovery{1,2} / notassess)+ 基线 CONTRACTGUARD;对照 0618 系列
- 结论一句话:**verified negative 恒为 0 的真因在最上游——Evidence Agent 几乎产不出合法证据 JSON(80–100% 落 fallback 空壳),而不是负向门禁 / prompt-relation 太严。昨天所有迭代都在调下游,信号在到达门禁前就已经没了。**

---

## 1. 症状

| run | reward 均值 | review_negative_verified | verified_actionable_negative_flaw | grounded 负向记录 |
|---|---|---|---|---|
| CONTRACTGUARD(基线,0618) | **0.650** | 0 | 0 | 0 |
| claimraw1 | 0.565 | 0 | 0 | 0 |
| claimraw2 | 0.612 | 0 | 0 | 0 |

- 整条 0619 系列 `review_negative_verified_count` 全 0,基线也 0;两个 claimraw 变体 reward 反而**低于基线**。
- claimraw2 八篇全 `final_decision=reject`,但 `es_flaw_density=0` —— 决策是 reject,背后**零 grounded flaw** 支撑,正是论文叙事最怕的"拒稿但拿不出经核验的缺陷"。
- claimraw1 positive 还回退:`real_strong_support_total` 38→28、`empirical_real_strong_support_count` 30→17、evidence 轮 39→31。

## 2. 根因:Evidence Agent JSON 输出可靠性

用系统自记的 `evidence_json_parse_status`(只统计真实证据轮,排除非证据轮的空状态):

| run | 真实证据轮 | json_valid | fallback | fallback 率 | evidence prompt_chars |
|---|---|---|---|---|---|
| claimraw2 | 32 | **0** | 32 | **100%** | ~6917 |
| claimraw1 | 31 | 2 | 29 | 94% | ~6701 |
| semanticfix1 | 29 | 0 | 28 | 97% | ~5659 |
| quotetask1 | 29 | 1 | 26 | 90% | ~5418 |
| quoteactive1 | 28 | 3 | 24 | 86% | ~5321 |
| claimgate1 | 27 | 2 | 24 | 89% | ~5227 |
| diagpendingfix_default(0618) | 44 | 1 | 35+ | 80%+ | ~9165 |
| targetguard(0618) | 18 | 1 | 16 | 89% | ~4190 |

`json_valid` 全程仅 0–3 条。失败类型(claimraw2):`no_json_object`=15(纯复读 prompt/schema)、`invalid_json`=13、`truncated_tagged_json`=3、`truncated_json_object`=1。

两个直接驱动因素:

1. **`max_tokens=768` 过低**(见 claimraw2 log:`model=mimo-v2.5 ... max_tokens=768`)。证据 prompt 5–7k 字符,模型却只能吐 ~768 token(≈2–3k 字符),raw_chars 均值已逼近上限 → 大量 `truncated_*` 与因截断导致的 `invalid_json`。
2. **prompt 膨胀**。0618 的 ~9k prompt 失败 61–68%,0619 砍到 ~5–6k 后降到 43–57%,`targetguard` 的 ~4.2k 最低(31%)。两头一夹,小模型把 schema/prompt 原样复读(连 manager 都把占位符 `"Worker Agent Name"` 填进了 `selected_agents`)。

> 每次"修复"往 prompt 堆规则,都在让小模型更崩 —— 这是个负反馈循环,也是"推进很多却没作用"的机制。

## 3. 为什么 positive 有量、negative 偏偏恒 0

同一个 ~90% JSON 失败,两侧待遇不同:

- **positive**:JSON 失败时由 quote-bank 兜底打捞(`first_support_fallback_turns`、`small_model_quote_bank_augmentation_count`),所以仍有几十条 grounded 支持,**把模型的失败掩盖了**。
- **negative**:同类"从 quote-bank 造负向"的打捞被(正确地)关掉以防造假(`quote_bank_salvage_generated_negative_count=0`)。于是负向**完全依赖模型吐出干净 JSON**,而这件事成功率 ~6%,其中能 ground 的负向几乎为 0。

因此:**负向门禁/relation 链(三层门禁 + 已知的 state.py:1100 author-limitation 漏点)目前根本没被触达**。红线当前"安全"只是因为上游什么都没产出,而不是门禁在起作用。

## 4. 修复方向(按杠杆排序)

1. **先治 JSON 可靠性,这是唯一应当先做的事:**
   - 抬高 `max_tokens`(768 → 至少 1536–2048),消除截断;
   - 大幅精简 evidence prompt(`targetguard` 证明 ~4.2k 能把失败率减半),把规则从 prompt 移进**已存在的确定性 verifier**,而不是继续堆文本;
   - 加强 JSON partial-recovery;若 API 支持,启用 JSON / 受约束解码。
2. **把 `evidence_json` fallback 率设为 dashboard headline KPI**;在它降到可接受(建议 <20%)之前,**冻结所有下游负向逻辑的调参** —— 现在负向信号被 ~90% 噪声埋着,任何 A/B 都不可信。
3. JSON 可靠之后再回到:负向形成质量、以及 state.py:1100 的 author-limitation 漏点修复(concrete_gap 通道叠加 `not _REVIEW_NEGATIVE_AUTHOR_LIMITATION_RE`)、prompt 的 golden-baseline 重构(消除 OFF≠baseline 漂移)。

## 5. 旁证与排除

- **claimraw1 的 positive 回退**源于它走 `hard_negative_discovery_override + recovery_recheck_exit_to_flaw_analysis`,`analyze_flaws` 4→16 抢占 evidence 轮 —— 即记忆中的 net-negative 模式;claimraw2 缓和但仍在基线下。
- **reward.py**(`_evidence_support_score` 改用 `build_decision_hygiene_view` 重算 + `real_claim_count`)只影响报告分与可比性,与 0-negative、JSON 失败**无因果关系,属正交**;但要注意跨版本 reward 可比性。
- **paper_text 不缺**:claimraw2 log 显示全文 30k–56k 字符已加载;claimraw1 的 `review_state.paper_text=0` 只是保存时未持久化。
