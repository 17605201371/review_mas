# Final Recommendation Policy v2 Final

## 定位

`Final Recommendation Policy v2` 是基于 clean 4B fulltest39 离线审计后的推荐口径。它替代“strong support 数量 -> accept”的粗规则，但不替代 runtime final decision。runtime `accept/reject` 仍只作为 health check。

## 输出标签

| 标签 | 使用条件 | binary 映射 |
| --- | --- | --- |
| `accept_like` | 暂不自动产生；需要 support-quality + hard-negative 人工核查通过后才能使用。 | 不自动映射。 |
| `borderline_positive` | 有 non-abstract、independent、empirical/table/method support，但尚未排除 false-accept 风险。 | 不映射 accept。 |
| `borderline_insufficient` | 有部分 support 或 stale/meta burden，但不足以形成可靠推荐。 | 不映射 accept。 |
| `reject_like` | 有 grounded major/critical flaw。 | 可映射 reject。 |
| `not_assessable` | 缺少足够证据、targetless unresolved 较多、或无法可靠 grounding。 | 不写成论文 weakness。 |

## V2 与 V1 的关键差异

V1 允许高精度 accept-like 作为正向推荐；V2 在 clean 4B 证据下更保守：support-quality rule 虽然恢复 2 个 accept，但同时产生 5 个 false accept，因此自动 `accept_like` 暂停，先输出 `borderline_positive`。

## Clean 4B 执行分布

| view | count |
| --- | ---: |
| accept_like | 0 |
| borderline_positive | 6 |
| borderline_insufficient | 12 |
| reject_like | 1 |
| not_assessable | 20 |

## 论文写法

论文中应明确：当前系统的二分类推荐尚未成熟，但 final-view 能把“有正向 evidence 但不足以安全 accept”的样本与“真正 grounded reject-like”样本区分开。这比 always-reject 更符合审稿辅助定位。

## 下一步

在正式主试验前，对 `borderline_positive` 样本做人工核查：确认 support 是否支撑核心贡献、是否存在未捕获的 hard-negative、是否应进入 paper case study。
