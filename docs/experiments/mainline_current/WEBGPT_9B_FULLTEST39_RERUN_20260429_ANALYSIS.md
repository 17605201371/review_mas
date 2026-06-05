# WEBGPT_9B_FULLTEST39_RERUN_20260429 Unified Analysis

## 结论
这次 9B fulltest39 rerun 已经有完整运行产物，但统一分析显示：它仍然不能直接作为“最终主试验成功结果”。主要原因不是模型不会生成 review，而是 runtime final decision 仍然全 reject，positive support 仍偏少且以 abstract/source-level 信号为主，criterion section 的 coverage/grounding 还不均衡。

更准确的定位是：这份结果可以进入论文的 9B 主线诊断表，但还需要配合 final-view hygiene / criterion-grounded decision view 做离线对照，不能只报告 runtime accept/reject。

## 1. Decision Health

| metric | value |
| --- | ---: |
| rows | 39 |
| gold_accept_count | 9 |
| gold_reject_count | 30 |
| predicted_accept_count | 0 |
| predicted_reject_count | 39 |
| accuracy | 0.7692 |
| macro_f1 | 0.4348 |
| accept_recall | 0.0000 |
| reject_recall | 1.0000 |
| avg_reward | 0.4284 |
| median_reward | 0.4794 |

false_reject_ids: `hj323oR3rw, QAAsnSRwgu, X41c4uB4k0, gzqrANCF4g, KI9NqjLVDT, 1HCN4pjTb4, LebzzClHYw, BXY6fe7q31, jVEoydFOl9`

解释：runtime recommendation 仍然是 39/39 reject，因此 accept recall 为 0。这个指标应作为 decision collapse 健康检查，而不是论文主贡献指标。

## 2. Positive Support Formation

| metric | value |
| --- | ---: |
| total_evidence | 98 |
| total_strong_support | 18 |
| real_strong_support | 15 |
| fallback_strong_support | 3 |
| unbound_strong_support | 0 |
| strong_support_binding_precision | 0.8333 |
| rows_with_2plus_real_strong_support | 4 |
| evidence_fallback_payload_count | 44 |
| evidence_parse_error_count | 22 |
| rows_with_fallback_evidence | 25 |

解释：real-claim strong support 已存在，但总量仍低；fallback strong support 没有成为主要问题，不过 fallback evidence / fallback extraction 仍然在 report 和 state 里可见。

## 3. Support Quality

| metric | value |
| --- | ---: |
| nonabstract_real_strong_support | 6 |
| empirical_real_strong_support | 1 |
| method_real_strong_support | 5 |
| table_figure_real_strong_support | 0 |
| rows_with_2plus_nonabstract_real_strong_support | 2 |

real strong support section distribution:

- `method`: 5
- `abstract`: 9
- `result_or_empirical`: 1

解释：support quality 仍是主瓶颈之一。即使有 strong support，也需要进一步区分 abstract-only、method、empirical/result/table 支持。

## 4. State Hygiene

| metric | value |
| --- | ---: |
| unresolved_count | 208 |
| evidence_gap_count | 69 |
| stale_gap_with_support_count | 13 |
| unsupported_with_strong_support_count | 3 |
| unsupported_with_2plus_strong_support_count | 1 |
| candidate_flaw_count | 16 |
| confirmed_flaw_count | 1 |
| critical_or_major_flaw_count | 17 |

解释：unresolved / evidence gaps / candidate flaws 仍然较多。后续仍应通过 final-view derived hygiene 处理 stale negative burden，而不是把 hygiene 放进 live state mutation。

## 5. Recovery Effectiveness

| metric | value |
| --- | ---: |
| recovery_attempt_turns | 73 |
| recovery_patch_mode_turns | 76 |
| recovery_patch_emitted_turns | 33 |
| recovery_patch_validated_turns | 71 |
| recovery_patch_committed_turns | 6 |
| rows_with_recovery_patch_emitted | 17 |
| rows_with_recovery_patch_committed | 4 |
| model_generated_commit_count | 1 |
| system_salvaged_commit_count | 5 |
| emission_to_commit_rate_turn_level | 0.1818 |

failure_code_distribution:

- `BLOCKED_BY_POLICY`: 62
- `OUTPUT_SCHEMA_MISSING`: 4
- `SUCCESS`: 6
- `INVALID_STATUS_TRANSITION`: 2
- `NO_EFFECT_PATCH`: 3

解释：recovery phase 和 patch emission 已经不是 0，但 turn-level emission-to-commit 仍低。现阶段不建议继续加 controller，应优先把 evidence/support/report/decision view 的指标收口。

## 6. Criterion Coverage / Grounding

| dimension | covered | coverage_rate | grounded | grounding_rate |
| --- | ---: | ---: | ---: | ---: |
| novelty_originality | 6 | 0.1538 | 6 | 0.1538 |
| significance_contribution | 35 | 0.8974 | 17 | 0.4359 |
| technical_soundness | 28 | 0.7179 | 13 | 0.3333 |
| empirical_adequacy | 22 | 0.5641 | 5 | 0.1282 |
| clarity_reproducibility | 9 | 0.2308 | 7 | 0.1795 |

avg_criterion_coverage_per_report: `2.5641`  
avg_criterion_grounding_per_report: `1.2308`

解释：significance 和 soundness coverage 较高，但 novelty / clarity coverage 偏低，empirical grounding 尤其弱。这说明网页版 GPT 提到的 criterion coverage/grounding 缺口是实质问题。

## 7. Meta Leakage

| metric | value |
| --- | ---: |
| criterion_meta_leakage_count | 0 |
| criterion_unsupported_critique_count | 0 |
| final_report_meta_term_rows | 17 |
| final_report_meta_term_rate | 0.4359 |

criterion_meta_leakage is conservative; final_report_meta_term_rows counts report text that explicitly mentions fallback/parse/excerpt/system artifacts.

解释：criterion-level meta leakage 的保守规则没有检出，但 final report 中显式出现 fallback/parse/excerpt/system 词的样本不少。论文里应把这作为 report hygiene 风险，而不是忽略。

## 8. Case-level Failure Summary

完整逐样本表见 `WEBGPT_9B_FULLTEST39_RERUN_20260429_CASE_TABLE.md`。主要标签分布如下：

- `no_real_strong_support`: 30
- `low_criterion_grounding`: 28
- `fallback_evidence_present`: 25
- `report_meta_terms`: 17
- `recovery_emitted_no_commit`: 13
- `stale_gap_with_support`: 9
- `false_reject`: 9
- `abstract_only_real_support`: 5
- `unsupported_with_strong_support`: 3
- `fallback_strong_support`: 3
- `recovery_attempt_no_patch`: 2

## 下一步建议

1. 这份 9B rerun 需要作为统一主线诊断结果保留，但不能单独宣称 final decision 成功。
2. 下一步应把 `final-view hygiene`、`support quality filter`、`criterion-grounded decision view` 作为离线对照接到同一份 9B final states 上，比较 runtime all-reject 与 derived decision view 的差异。
3. 不建议现在回到 sticky/throttle/gate，也不建议直接调 accept/reject 阈值。当前最值的一刀是统一决策视图与报告质量评估，而不是继续 controller。
