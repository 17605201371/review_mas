# Hard-Negative Diagnosis A/B 审计 (2026-06-16)：net-negative，不进主线

## 设置（干净 A/B）

- baseline: `mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_..._172713_merged20.jsonl`（hardneg_diagnosis=off）
- candidate: `mimo_v25_negqty_recoverycap_guard3_qhyg_hardnegdiag_hardneg20_..._184705.jsonl`（hardneg_diagnosis=1）
- 两者 **同码**（meta: `code_commit=3b97956 code_dirty=dirty`，含本会话点1/点3/收紧修复）、同 qhyg、同数据集、各 **20/20** 完成。唯一差异 = `DRMAS_HARDNEG_DIAGNOSIS`。
- 全套 dashboard 见 `HARDNEGDIAG_AB_DASHBOARD_20260616.md`。

## 结论：跨指标 net-negative，只有保护线守住

| 指标 | qhyg_base | hardnegdiag | delta |
|---|---:|---:|---:|
| avg_reward | 0.4979 | 0.4540 | **-0.044** |
| real_strong_support_total | 75 | 53 | **-22** |
| empirical_real_strong_support | 58 | 41 | -17 |
| claims_with_2plus_independent | 36 | 26 | -10 |
| negative_evidence_candidate | 4 | **0** | -4 |
| verified_negative_flaw | 4 | **0** | -4 |
| verified_actionable_negative_flaw | 3 | **0** | -3 |
| verified_potential_concern | 3 | **0** | -3 |
| mark_contested_commit / contested_relation_effective | 3 | **0** | -3 |
| recovery_attempted / committed | 4 | **0** | -4 |
| recovery_effective_repair | 3 | **0** | -3 |
| 保护线（leakage / nonreal_strong / harmful_recovery / unlinked …） | PASS | PASS | 0 |

即：诊断 ON 把整条 **负向→contested→recovery 流水线打到 0**，同时**正向 support 也降**（75→53）。安全没破（因为它只是"做得更少"，没做危险的事）。

## 根因（确定性，非方差）：override 被改路由到 Critique，evidence 形成被挤掉

turn-log action 分布（确凿）：

| action_type | baseline | hardnegdiag |
|---|---:|---:|
| `request_evidence_recheck`（Evidence Agent） | 56 | **10** |
| `analyze_flaws`（Critique Agent） | 23 | **80** |
| verify_evidence | 21 | 22 |
| extract_claims | 27 | 26 |

`hard_negative_discovery_override` 在 ON 分支被路由成 `analyze_flaws`/Critique（而非 baseline 的 `request_evidence_recheck`/Evidence）。后果链：
1. ~46 个本该 Evidence-Agent 做 evidence-recheck（形成/核验负向证据 + 补正向）的轮次，变成 Critique 的 model-judgment 诊断；
2. Critique 的诊断产出的是 `diagnosis_pending_verification` 候选，**没有后续 Evidence 核验去绑定 verified negative evidence** → verified_negative=0 → contested=0 → recovery=0；
3. 丢掉的 evidence-recheck 轮次 → 正向 support 75→53。

**这与 P-A compact 的失败完全同型**（见 `P_A_COMPACT_NEGATIVE_PASS_AUDIT_20260616.md`：compact 只派 Critique→既不形成 verified negative，又挤压 support）。两次都证明：**把 negative discovery 这轮交给 Critique 的 model-judgment 去"想"，而不是交给 Evidence Agent 去"找+核验 quote"，是 net-negative。**

## 判断与下一步

- **diagnosis ON 不进主线**，保持默认关（已是默认）。本审计 + dashboard 留作第二个"此路不通"的反例。点1/点3/收紧的代码修复本身是对的（实验干净、保护线守住、诊断目标不再被 fallback 饿死也不再过宽）——它们让我们拿到了一个**干净的负向结论**，这就是它们的价值。
- 真正可走的方向仍是路线图里的 **P-B（尚未实现）**：**不替换** evidence-recheck 这轮，而是用 claim-centric 诊断去**重排 verify_evidence/recheck 的 target 优先级**（优先核验有缺口的真 claim），让 Evidence Agent 仍然负责形成+核验负向证据。数据明确显示：形成 verified negative + 正向 support 的是 Evidence-Agent 的 evidence-recheck，不是 Critique 的 model-judgment。
- 严谨性：这是单 seed 对单 seed，reward 差(-0.044)单独看可能落在方差内；但负向/contested/recovery 全部归零 + action 分布 56→10 / 23→80 是**机制性**塌缩，不是采样噪声。若要正式写进论文反例可再补多 seed，但方向已清楚。
