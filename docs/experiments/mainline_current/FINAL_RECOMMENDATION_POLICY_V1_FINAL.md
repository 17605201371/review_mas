# Final Recommendation Policy v1 Final

## 定位

`Final Recommendation Policy v1 Final` 是当前 `Mainline-Final-v1` 的主试验前推荐口径冻结文件。它不是 runtime prompt，不改 live `ReviewState`，不把 novelty / soundness / empirical 等维度裸接入 accept/reject。它只定义论文结果层如何解释最终推荐。

核心原则：

> binary accept/reject 只作为 health check；论文主输出采用 evidence-grounded final recommendation view。

## 输入层

本 policy 只使用已经生成的 final-view / offline 派生信息：

1. `ReviewState` 的最终 evidence / flaw / unresolved / gap 状态。
2. support quality view：real-claim support、non-abstract support、empirical support、independent support groups。
3. invalid-binding / fallback-bound / unbound support 过滤结果。
4. criterion coverage / grounding：novelty、significance、technical soundness、empirical adequacy、clarity。
5. flaw lifecycle / meta-leakage view：confirmed grounded flaw、ungrounded candidate、system/meta flaw、excerpt limitation。

不使用：

- raw fallback-bound strong support 作为 accept 信号；
- ungrounded candidate flaw 作为 hard reject；
- excerpt/system limitation 作为 paper weakness；
- not-assessable criterion 作为负面证据。

## 输出标签

正式论文结果层使用五类 recommendation view：

| 标签 | 含义 | 是否映射为 accept |
| --- | --- | --- |
| `accept_like` | 有有效 real-claim support、足够 support quality、无 grounded hard blocker。 | 只在 strict 分析中可映射为 accept。 |
| `borderline_positive` | 有正向证据，但 support depth / independence / empirical adequacy 或 blocker 检查不足。 | 不直接映射为 accept。 |
| `borderline_insufficient` | 有部分信号，但证据不足或 state burden 仍明显。 | 不直接映射为 accept。 |
| `reject_like` | 存在 grounded hard blocker 或缺乏有效 support 且负面证据充分。 | 可映射为 reject。 |
| `not_assessable` | 证据/上下文不足以形成可靠推荐。 | 不应强行当作论文 weakness。 |

## `accept_like` 的最低条件

`accept_like` 不是 strong-support-count 规则，必须满足：

1. 有 valid real-claim strong support。
2. support 不是 fallback-bound / invalid-bound / unbound。
3. 至少有 non-abstract support；更理想是 empirical / method / result / table / figure 证据。
4. support 有一定独立性，不能只重复同一个 abstract self-claim。
5. 至少一个正向 criterion 是 grounded，而不是 final report 泛化措辞。
6. 没有 grounded confirmed critical flaw。
7. 没有 grounded major technical soundness 或 empirical adequacy blocker。

如果 1-5 有正向信号但 6-7 不完全明确，应降为 `borderline_positive`。

## `reject_like` 的允许依据

只能由以下 grounded 信号支持：

1. confirmed critical flaw；
2. grounded major technical soundness flaw；
3. grounded major empirical adequacy flaw；
4. core claim 被 grounded contradiction 反证；
5. 缺少有效 real-claim support 且存在可靠负面证据。

不能由以下信号单独触发：

- candidate flaw；
- unresolved item；
- stale evidence gap；
- fallback artifact；
- recovery failure；
- system/excerpt limitation；
- novelty not-assessable。

## `borderline` 与 `not_assessable` 的角色

`borderline_positive` 和 `not_assessable` 是当前论文系统的重要输出，不是失败项。它们表达的是审稿辅助系统的证据边界：

- 有正向 support 但不足以安全 accept，应为 `borderline_positive`。
- 缺少必要上下文、criterion 无法 grounding，应为 `not_assessable`。
- 不应为了提高二分类 accuracy，把这两类硬映射为 accept 或 reject。

## 当前 dry-run 指标快照

来自 `MAINLINE_FINAL_V1_DRY_RUN_REPRODUCIBILITY.md`：

| 指标 | 值 |
| --- | ---: |
| runtime rows | 39 |
| runtime final decision | reject=39 |
| final recommendation `accept_like` | 1 |
| final recommendation `borderline_positive` | 12 |
| final recommendation `not_assessable` | 22 |
| final recommendation `borderline_insufficient` | 3 |
| final recommendation `reject_like` | 1 |
| real strong support total | 37 |
| non-abstract support total | 18 |
| empirical support total | 5 |

## 论文写法

论文中应明确：

1. runtime accept/reject collapse 是 health-check 发现，不是系统唯一目标。
2. 传统二分类 recommendation 对当前任务过粗，会掩盖 evidence grounding 和 uncertainty。
3. 本文主张用 final-view recommendation 表达证据充分性、状态卫生、criterion grounding 和不确定性。
4. `accept_like` 是高精度正向推荐；`borderline` 和 `not_assessable` 是审稿辅助系统应保留的安全输出。

## Calibration v1 更新

`Final Recommendation Calibration v1` 对当前 accept collapse 做了离线弥补：

- 9B fulltest39 上 `calibrated_high_precision` 恢复 2 个 accept（`KI9NqjLVDT`, `LebzzClHYw`），false accept 为 0。
- `calibrated_balanced` 恢复 3 个 accept，但引入 2 个 false accept（`kam84eEmub`, `ye3NrNrYOY`）。

因此冻结口径调整为：

- high-precision 通过：标为 `accept_like`。
- balanced 通过但 high-precision 未通过：标为 `borderline_positive`，不直接映射 accept。
- support-count-only 与 sim4 accept-like 都不能作为正式 accept 规则。

## 当前冻结结论

本 policy 可以作为 `Mainline-Final-v1` 主试验 dry-run 的推荐口径。下一步若继续实验，应只做最终复现 / confirmation，不再新增 sticky、throttle、progression gate 或 live state hygiene mutation。
