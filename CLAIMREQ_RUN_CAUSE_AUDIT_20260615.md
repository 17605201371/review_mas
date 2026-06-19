# Claim Requirement Run Cause Audit 2026-06-15

## 输入

- Candidate: `mimo_v25_claimreq_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_144450.jsonl`
- Main baseline: `mimo_v25_negqty_recoverycap_guard3_qhyg_hardneg20_mt7_b4w2_api4_r5t600_20260615_003753.jsonl`
- Multi-seed baseline group: default x3 and qhyg x3, cropped to the common 16 papers.

## 总结论

这轮结果不满意不是因为 API 没跑完，也不是因为 quote grounding 失效。20/20 完成，保护线 PASS，missing verified quote 和 final leakage 都为 0。

主要问题是：claim requirement 诊断层被接入后，Evidence Agent 更常输出 unresolved/question-only，而不是补出对应的 verified evidence；同时本轮单 seed 的 support 生成质量低于 qhyg 多种子区间下沿，因此不能简单归因于随机波动。

## 关键对比：20 篇完整 run

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---:|---:|---:|
| `real_strong_support_total` | 100 | 82 | -18 |
| `independent_support_group_total` | 100 | 82 | -18 |
| `claims_with_2plus_independent_support` | 47 | 39 | -8 |
| `empirical_real_strong_support_count` | 76 | 63 | -13 |
| `negative_evidence_candidate_count` | 12 | 12 | 0 |
| `verified_actionable_negative_flaw_count` | 8 | 7 | -1 |
| `negative_type_scope_overclaim` | 7 | 2 | -5 |
| `state_contamination_count` | 0 | 1 | +1 |
| `evidence_gap_open_count` | 1 | 6 | +5 |
| `recovery_effective_repair` | 8 | 6 | -2 |
| `recovery_no_effect_commit` | 1 | 1 | 0 |

## 多种子同批 16 篇对比

Candidate 低于 qhyg 三次 seed 的 support 区间下沿：

| metric | qhyg min-max | claimreq |
|---|---:|---:|
| `avg_reward` | 0.5513-0.5629 | 0.5388 |
| `real_strong_support_total` | 69-82 | 61 |
| `independent_support_group_total` | 68-82 | 61 |
| `empirical_real_strong_support_count` | 49-62 | 46 |
| `claims_with_2plus_independent_support` | 32-39 | 29 |
| `evidence_gap_open_count` | 0-4 | 6 |
| `recovery_effective_repair` | 3-7 | 3 |
| `state_contamination_count` | 0-0 | 1 |

因此这轮下降不能只解释为普通 seed 方差。

## 轮次与上下文挤压

不是传统意义的总轮次挤压：

| turn metric | qhyg_003753 | claimreq_144450 |
|---|---:|---:|
| total turns | 135 | 137 |
| Claim Agent turns | 26 | 26 |
| Evidence Agent turns | 89 | 87 |
| Critique Agent turns | 25 | 30 |
| `verify_evidence` actions | 29 | 26 |
| `analyze_flaws` actions | 14 | 19 |
| `challenge_previous_hypothesis` actions | 10 | 11 |

实际变化是 action 分配从 evidence verification 向 critique/recovery 轻微偏移，Evidence Agent turn 少 2，Critique turn 多 5。

但存在 observation 裁剪瓶颈：重建 Evidence Agent observation 后，87/87 个 evidence turns 都达到约 4190 字符并被截断，且 `Evidence-Relevant Paper Excerpt` 没进入最终 observation。Quote Bank 仍进入 observation，因此当前 evidence 主要依赖 quote bank，而不是完整 paper excerpt。这个不是本轮独有问题，但 claim requirement block 会继续占用同一个 4200 字符预算。

## Evidence Agent 输出变化

| evidence behavior | qhyg_003753 | claimreq_144450 |
|---|---:|---:|
| evidence turns | 89 | 87 |
| evidence payload items | 124 | 99 |
| evidence question-only turns | 21 | 30 |
| payload real strong | 32 | 27 |
| final-view payload support | 96 | 77 |

这是本轮 support 下降的直接原因：agent 看到 gap 后更倾向于提 unresolved question，而不是从 Quote Bank 复制并绑定 required evidence。

## Claim 前端质量问题

部分论文 claim extraction 仍退化为 fallback/salvage claim。例如 `7Dub7UXTXN` 在 candidate 中出现 6 个 `claim-paper-fallback-*`，baseline 中是正常 `claim-1/2/3`。这类退化会影响 support 绑定和 requirement gap 解释。

这说明 claim requirement 层不是唯一原因；小模型 claim extraction/JSON salvage 仍是上游不稳定源。

## 已发现并修复的问题

本轮 API run 的 final report 里 `claim-evidence gap` 20/20 可见，原因是 requirement audit 原本把 `claim-paper-context-*` / `claim-paper-fallback-*` 也算入 gap。

已在 `state.py` 修复：claim requirement audit 现在只统计 auditable real paper claims，排除 context/fallback/salvage scaffold claims。离线重算后：

| metric | qhyg_003753 | claimreq_144450 | delta |
|---|---:|---:|---:|
| `claim_requirement_missing_total` | 14 | 13 | -1 |
| `papers_with_requirement_gaps` | 4 | 3 | -1 |
| `primary_claims_with_requirement_gaps` | 10 | 5 | -5 |

当前保存的 144450 final reports 仍是修复前生成的，因此不能作为干净 report 结论使用；应以后续 rerun 或离线重渲染为准。

## 根因排序

1. Evidence Agent 对 claim requirement gap 的响应策略不对：它把 gap 当成“提问/无法确认”，没有被强约束为“先尝试从 Quote Bank 找 required evidence”。
2. Evidence observation 已经长期在 4200 字符裁剪上限，paper excerpt 被挤掉；claim requirement block 增加了认知负担，但不是唯一新增挤压源。
3. Manager action 分配轻微偏向 Critique/Recovery，`verify_evidence` 少 3 次，导致 support 机会减少。
4. 小模型 claim extraction 仍会产生 fallback/salvage claim，影响后续绑定和 gap 诊断。
5. 本轮一处 report-layer bug 已修：context/fallback claim 不再进入 claim requirement gap。

## 下一步建议

不要继续直接扩大 claim requirement 展示。应改为：

1. 把 `claim_requirement_gaps` 从“报告展示优先”改成“Evidence Agent 的 targeted evidence search task”。
2. Evidence Agent 看到 requirement gap 时必须先输出 one required-evidence attempt：优先 quote bank 中的 table/result/baseline/ablation quote；只有找不到才 unresolved。
3. 对 requirement gap block 做压缩，避免占用 quote bank 和 excerpt 预算。
4. 修 claim extraction fallback/salvage 的诊断：raw-salvaged claim 可以保留，但不能驱动 final report gap。
5. 下一轮先做离线 prompt/observation 重排，不急着重跑 20 篇。
