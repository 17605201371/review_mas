# 路线A:负向证据 claim-反驳白名单 + Codex 双 agent 互审闭环(2026-06-20)

> 承接 `NEGATIVE_RECALL_3GATE_FIX_AND_AUDIT_20260620.md`(P0/三关/路线3)。本轮经 Codex
> 双 agent 互审收敛到**路线A(判据升维)**,根治负向假阳性。已 push origin/main `055f2d2`。

## 0. TL;DR
verified negative 不再"凭负向词/type 判定",改为**只认反驳本文 claim 的确定信号**——从根上区分"作者自报内部结果"与"审稿人发现的缺陷",根治 ablation/variant/control/动机/prior-work 假阳性的逐类打地鼠。终局=**quote-grounded(极严格,0 假阳性)+ deterministic coverage gap(recall 主力)双维度**。

## 1. Codex 双 agent 互审闭环(本轮)
1. 我跑 route3 hardneg20,自动指标报 1 条 `review_negative_verified`。
2. **Codex 审日志**:那条是 Critique 把作者动机句(`"Worse yet, we found increased heterogeneity...distilled local virtual data"` 后接 `"We aim to alleviate..."`)误当方法缺陷 = problem-motivation 假阳性。
3. 我核实(论文原文确是 problem-motivation 结构)→ 修 guard + 回归测试 + 离线 replay 确认。
4. 重跑又**自查出** prior-work `\cite{x2024}` 批评假阳性 → 修。
5. 再重跑暴露 ablation/variant/control 假阳性。用户 + Codex 指出:**"不能光靠规则;这是 ablation/control/variant/tradeoff 结果被误当 reviewer-discovered negative"**。
6. Codex 提三层架构(reviewer_defect_relation + defect_hypothesis + **Reviewer diagnosis 层由模型判**)。
7. 我指出 **model diagnosis 踩 Do-Not-Retry**(`DRMAS_HARDNEG_DIAGNOSIS` 两次证伪 net-negative),收敛到**路线A**:保留 Codex"分离 observation/flaw"洞察,但判定用**确定性 claim-evidence 白名单**,不引入 model judgment。用户拍板走 A。

## 2. 路线A判据(`state.py` `_assess_review_negative_relation`)
actionable 类型不再凭 type 免检;`review_negative_verified` 仅当 **`contradicts_paper_claim`**(四选一):
1. `own_method_underperforms` — 本文方法不如 baseline/SOTA(数据打脸,双向措辞 `_OWN_METHOD_WORSE_THAN_BASELINE_RE`)
2. `concrete_gap` — 本文缺必需 baseline/ablation/evaluation
3. `direct_contradiction` 措辞 — fail to prove / does not generalize 等直接反驳 claim
4. `broad_claim + scope_relation` — overclaim 被范围限制削弱

其余 negative-looking quote → `insufficient_claim_relation`(paper_observation)。作者自报 ablation/variant/control/tradeoff/动机**因不反驳本文 claim 自动出局**,不需逐类正则。

## 3. 双维度终局
| 维度 | 语义 | hardneg20 |
|---|---|---|
| quote-grounded verified | 只认反驳本文 claim,极严格 | ≈0(论文不自我批评),**0 假阳性** |
| **verified_coverage_gap(路线3)** | primary claim 缺必需证据类型,确定性审计,与真审稿吻合 | **~12(recall 主力)**,严格平行、不混计数 |

## 4. 验证
- 焦点测试 **556 全绿**(+1 路线A ablation 回归测试)。
- **离线 replay**:三个旧 hardneg20 run 旧判 verified 的**全部 5 条假阳性**(动机/ablation/variant/control/prior-work)在新代码下**全部不再 verify**。
- **routea hardneg20 run**:0 假阳性 + coverage gap 12 + 硬约束(harmful_contamination/recovery_harmful/no_effect)全 0。
- 端到端确认真负向(数据打脸/缺证据/直接反驳/overclaim)仍 verify。

## 5. 下一步建议(给接力)
- **提高 recall**:深挖 coverage gap(路线3)产出更多与真审稿吻合的缺证据负向;或增强 `result_claim_mismatch` 的确定性判定(结果落在 claim 声称范围内且矛盾)。
- **不要**:回到 model-judgment diagnosis(Do-Not-Retry 已两次证伪);逐类堆假阳性正则(路线A已用白名单根治)。
- 论文叙事:系统"构造可核验的审稿诊断(两维:claim-反驳 + 确定性缺证据覆盖)",不是"抓负面词"。

## 6. 关键 commit(均已 push origin/main)
- `055f2d2` 路线A claim-反驳白名单
- `473f3f3` prior-work `\cite` guard
- `8de78a6` 路线3 coverage gap 独立维度 + problem-motivation guard
- `f44c8e4` 三关委婉负结果识别
- `6ce54d6` P0 JSON 修复 / `ae178bb` verified-negative gate 硬化
