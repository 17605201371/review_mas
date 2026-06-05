# CRITERION_COVERAGE_GROUNDING_9B_FULLTEST39

## 输入与定位

- 输入文件：`WEBGPT_9B_FULLTEST39_RERUN_20260429.jsonl`
- 模型/设置：9B, S4, fulltest39, `max_turns=8`, `max_model_len=3072`
- 本文件是离线 criterion coverage / grounding 审计，不修改 runtime、final decision、prompt 或 ReviewState。
- 目的：判断 9B final report 是否覆盖真实审稿维度，以及这些维度是否有 evidence grounding。

## 总体结论

网页 GPT 的判断成立：criterion-aware report 不能只看“是否生成了 criterion section”，还必须审计覆盖率和 grounding。

本轮 9B runtime 仍然是 `reject=39/39`，说明 final decision 层仍然 collapse；criterion 维度应作为论文中的报告质量/诊断指标，而不是现在直接接入 accept/reject 规则。

关键发现：

- `significance_contribution` 和 `technical_soundness` 覆盖较高，但 `novelty_originality` 与 `clarity_reproducibility` 覆盖很低。
- `empirical_adequacy` 覆盖到 `22/39`，但 grounded 只有 `5/39`，说明系统会谈实验充分性，但经常缺少稳定证据链接。
- 当前启发式未检测到 unsupported critique / meta-leakage，但这只能说明显式泄漏不明显，不能证明 criterion grounding 已经充分。
- 因此下一步更适合做 criterion-aware final report / grounding schema，而不是 criterion-based final decision。

## Coverage 统计

- Rows: `39`
- Average covered criteria per report: `2.564`

| criterion | covered_rows | coverage_rate |
| --- | ---: | ---: |
| Novelty / Originality | 6 | 0.1538 |
| Significance / Contribution | 35 | 0.8974 |
| Technical Soundness | 28 | 0.7179 |
| Empirical Adequacy | 22 | 0.5641 |
| Clarity / Reproducibility | 9 | 0.2308 |

Coverage 读法：

- `Significance / Contribution` 覆盖最好，达到 `35/39`。
- `Technical Soundness` 次之，达到 `28/39`。
- `Novelty / Originality` 只有 `6/39`，`Clarity / Reproducibility` 只有 `9/39`，这两项是当前报告维度最明显短板。

## Grounding 统计

| criterion | grounded_rows | grounded_rate | unsupported_critique_count | not_assessable_rows |
| --- | ---: | ---: | ---: | ---: |
| Novelty / Originality | 6 | 0.1538 | 0 | 0 |
| Significance / Contribution | 17 | 0.4359 | 0 | 0 |
| Technical Soundness | 13 | 0.3333 | 0 | 0 |
| Empirical Adequacy | 5 | 0.1282 | 0 | 0 |
| Clarity / Reproducibility | 7 | 0.1795 | 0 | 0 |

Grounding 读法：

- `Significance / Contribution` grounded 最高，但也只有 `17/39`。
- `Technical Soundness` grounded 为 `13/39`，低于其 coverage `28/39`。
- `Empirical Adequacy` coverage 是 `22/39`，但 grounded 只有 `5/39`，这是最值得警惕的 gap。
- `Novelty / Originality` 和 `Clarity / Reproducibility` 本身 coverage 就低，grounding 自然也低。

## Meta-Leakage 与 Unsupported Critique

本轮启发式统计中：

- unsupported criterion critique: `0`
- criterion-level meta leakage: `0`

这个结果不能过度解释为“完全没有无证据批评”。当前脚本主要抓显式关键词和明显泄漏，因此更适合作为保守下界。论文表述应写成：

> We did not detect explicit criterion-level meta-leakage under our rule-based audit, but grounding coverage remains limited, especially for empirical adequacy.

## 代表案例

下面列出部分具有诊断意义的 case。

| paper_id | gold | pred | covered_criteria | grounded_criteria | unsupported_critiques | meta_leakage | summary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X41c4uB4k0 | accept | reject | significance_contribution,technical_soundness,empirical_adequacy |  |  |  | covered=3, grounded=0, unsupported=0, meta=0 |
| gzqrANCF4g | accept | reject | significance_contribution,empirical_adequacy |  |  |  | covered=2, grounded=0, unsupported=0, meta=0 |
| KI9NqjLVDT | accept | reject | significance_contribution,technical_soundness,empirical_adequacy,clarity_reproducibility |  |  |  | covered=4, grounded=0, unsupported=0, meta=0 |
| 1HCN4pjTb4 | accept | reject | significance_contribution |  |  |  | covered=1, grounded=0, unsupported=0, meta=0 |
| LebzzClHYw | accept | reject | significance_contribution,technical_soundness,empirical_adequacy |  |  |  | covered=3, grounded=0, unsupported=0, meta=0 |
| jVEoydFOl9 | accept | reject | significance_contribution |  |  |  | covered=1, grounded=0, unsupported=0, meta=0 |
| WpXq5n8yLb | reject | reject | significance_contribution,technical_soundness,empirical_adequacy,clarity_reproducibility | significance_contribution,technical_soundness,empirical_adequacy,clarity_reproducibility |  |  | covered=4, grounded=4, unsupported=0, meta=0 |
| cklg91aPGk | reject | reject | significance_contribution,technical_soundness,empirical_adequacy,clarity_reproducibility | significance_contribution,technical_soundness,clarity_reproducibility |  |  | covered=4, grounded=3, unsupported=0, meta=0 |
| aTBE70xiFw | reject | reject | novelty_originality,significance_contribution,technical_soundness,empirical_adequacy,clarity_reproducibility | novelty_originality,technical_soundness,clarity_reproducibility |  |  | covered=5, grounded=3, unsupported=0, meta=0 |
| kam84eEmub | reject | reject | novelty_originality,significance_contribution,technical_soundness,empirical_adequacy | novelty_originality,significance_contribution,technical_soundness |  |  | covered=4, grounded=3, unsupported=0, meta=0 |

案例读法：

- 一些 gold accept 样本仍然是 reject，并且 criterion grounding 很弱，例如 `X41c4uB4k0`, `gzqrANCF4g`, `KI9NqjLVDT`, `1HCN4pjTb4`, `LebzzClHYw`, `jVEoydFOl9`。这说明 accept 侧不是单纯 decision 阈值问题，而是 positive support / criterion grounding 仍不足。
- 一些 reject 样本 criterion coverage/grounding 较强，例如 `WpXq5n8yLb`, `cklg91aPGk`, `ZHr0JajZfH`, `aTBE70xiFw`, `kam84eEmub`。这说明 high criterion coverage 不是 accept 的充分条件，criterion 应先作为报告质量维度，而不是 final decision rule。

## 对网页 GPT 判断的结论

网页 GPT 说“criterion-aware report 还缺质量审计”是准确的。已有 criterion-aware rendering 只能证明报告结构更像审稿，但不能证明：

- novelty / soundness / empirical / clarity 等维度都被充分覆盖；
- 每个维度判断都有 evidence grounding；
- empirical weakness 不是由上下文不足或系统限制误写出来；
- criterion section 可以安全影响 final decision。

这份 9B 审计显示，报告维度 coverage 和 grounding 仍然不均衡，因此 criterion 现在应进入论文的“报告质量分析”和“诊断指标”，不应进入 runtime decision。

## 下一步建议

下一步建议保持克制：

1. 保留 criterion coverage / grounding audit 作为论文指标。
2. 如果继续工程优化，优先做 `Criterion Grounding Linker` 或 `Criterion-Aware Final Report Section`，目标是提高 evidence-grounded criterion coverage。
3. 不要把 low novelty / weak empirical adequacy 直接接入 final decision。
4. runtime final decision 仍只作为 health check；论文主结论应围绕 evidence binding、state hygiene、support quality、criterion-grounded reporting。
