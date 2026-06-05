# Mainline-Final-v1 4B Fulltest39 Dry Run Report

## 结论

本报告是主试验前 dry run，不新增模型推理。结果显示：runtime 输入卫生和 evidence binding 已经比早期稳定，但 final decision 仍然 reject-skew，且少量 accept 可能是 false accept；主要论文结论不应建立在 accept/reject accuracy 上，而应报告 evidence binding、support quality、final-view hygiene、criterion grounding 与 meta-leakage。

## Decision Health

| dataset | accuracy | accept recall | reject recall | macro-F1 | predicted accept |
|---|---:|---:|---:|---:|---:|
| retained integrated | 0.8205 | 0.1250 | 1.0000 | 0.5604 | 1 |
| isolation v1.1 | 0.8205 | 0.1250 | 1.0000 | 0.5604 | 1 |

## Evidence / Support Quality

| dataset | real strong | nonabstract strong | empirical strong | method | table/figure | ablation | independent groups | claims 2+ independent | fallback strong | fallback payload rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| retained integrated | 49 | 49 | 15 | 12 | 15 | 1 | 44 | 2 | 0 | 0.0000 |
| isolation v1.1 | 49 | 49 | 15 | 12 | 15 | 1 | 44 | 2 | 0 | 0.0000 |

## State / Recovery / Flaw View

| dataset | unresolved | evidence gaps | flaws | patch emitted | patch committed | rows any commit | broad target turn rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| retained integrated | 269 | 110 | 48 | 96 | 1 | 1 | 0.6447 |
| isolation v1.1 | 269 | 110 | 48 | 96 | 1 | 1 | 0.6447 |

## Final-View Flaw Lifecycle

- derived labels: `{'borderline': 15, 'not_assessable': 18, 'reject_like': 6}`
- strict recovered accepts: `[]`
- strict false accepts: `[]`
- 解读：flaw lifecycle 不恢复 strict accept，但把大量样本从 hard reject 转成 borderline / not_assessable，说明 report 层必须区分论文缺陷与系统/截断/未验证候选缺陷。

## Criterion Coverage / Grounding

| criterion | coverage rate | grounded rate |
|---|---:|---:|
| `novelty_originality` | 1.0000 | 1.0000 |
| `significance_contribution` | 1.0000 | 0.9744 |
| `technical_soundness` | 1.0000 | 0.9231 |
| `empirical_adequacy` | 1.0000 | 0.8462 |
| `clarity_reproducibility` | 1.0000 | 1.0000 |

## Controller / Metric Hygiene

| dataset | evidence JSON status turns | invalid/missing JSON | fallback-used status | progression gate turns | support formation pass turns | legacy controller active turns |
|---|---:|---:|---:|---:|---:|---:|
| retained integrated | 153 | 0 | 0 | 0 | 0 | 0 |
| isolation v1.1 | 153 | 0 | 0 | 0 | 0 | 0 |

注意：`invalid/missing JSON` 只统计 `no_json_object` / `invalid_json` / `truncated_tagged_json`，不再把所有 evidence status turn 误命名为 parse errors。`legacy controller active turns` 用于暴露 sticky/progression gate 是否仍污染主线解释。

## Go / No-Go

当前建议：可以进入 `Mainline-Final-v1` 论文主线收口和 9B 小确认，但不要把当前 4B fulltest39 当作正式主实验结果。正式主实验前应先固定 unified metrics，并把 final-view flaw lifecycle / criterion grounding 作为 report/hygiene 层输出，同时清理或明确保留旧 controller。

不要做：Support Formation Pass runtime、Evidence Context v3、sticky/throttle/gate、live state hygiene mutation、final decision 阈值硬调。
