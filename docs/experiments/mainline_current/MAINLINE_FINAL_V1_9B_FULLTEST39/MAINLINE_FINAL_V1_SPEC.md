# MAINLINE_FINAL_V1_SPEC

## 定位

`Mainline-Final-v1` 是当前论文主线的冻结口径。它的目标不是继续追加 controller，而是把已经证明有效的 evidence / state / report 组件收束成可复现的主试验 pipeline。

## Runtime 主线组件

- `p25.1 + explicit recovery phase` 保留版。
- Evidence Context / Empirical Structuring：让 Evidence Agent 看到更有效的正文证据区域。
- Evidence Binding Robustness：强约束 evidence 绑定到真实 claim，fallback/unbound support 不进入 real support。
- Evidence JSON Robustness：减少 JSON parse failure 与 fallback payload 污染。
- Config alignment / observability：固定 `max_turns`、model、subset、sampling 等关键运行口径。

## Final-view / Offline 层

- Derived hygiene / recommendation view：只在最终解释层使用，不改 live `ReviewState`。
- Support quality audit：区分 real / non-abstract / empirical / independent support。
- Hard-negative grounding audit：区分 grounded paper weakness、context limitation、targetless unresolved、unverified negative。
- Criterion-aware final report rendering：生成 novelty、significance、soundness、empirical、clarity 五个维度的报告段落。

## 暂停且不进入主线的分支

- target sticky 系列。
- progression throttle / progression gate 系列。
- support formation pass 作为当前主线控制器。
- live state hygiene mutation。
- final decision 阈值硬调。
- 全局 fallback suppression。

## 决策口径

Runtime binary accept/reject 只作为 health check。论文主输出采用 final-view recommendation：

- `accept_like`
- `borderline_positive`
- `borderline_insufficient`
- `not_assessable_*`
- `reject_like`

其中 `borderline_positive` 不映射为 accept；它表示已有正向证据但仍需人工审查。
