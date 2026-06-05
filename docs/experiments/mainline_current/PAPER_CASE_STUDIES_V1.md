# Paper Case Studies v1

## 目的

本文件把 `Final Recommendation View v1` 的代表样本转成论文可写的 case study。核心论点是：多类 recommendation view 比硬二分类更适合当前 evidence-grounded review assistance。

## High-precision accept-like: `KI9NqjLVDT`

- gold decision: `accept`
- final recommendation view: `accept_like`
- support summary: `real=2, nonabs=2, ind=2, emp=0`
- positive grounded criteria: `significance_contribution, empirical_adequacy`
- hard negative: `False`

**解释**：这是当前系统最可信的正向样本：真实 claim strong support、non-abstract support 和独立 support 都达到最低安全条件，并且有 grounded empirical adequacy。它说明系统不是完全没有 accept-like 能力，而是只能在证据质量足够时输出高精度正向推荐。

## Borderline positive gold accept: `BXY6fe7q31`

- gold decision: `accept`
- final recommendation view: `borderline_positive`
- support summary: `real=2, nonabs=1, ind=2, emp=0`
- positive grounded criteria: `significance_contribution, clarity_reproducibility`
- hard negative: `False`

**解释**：该样本是 gold accept，但系统只给 borderline_positive。原因是正向证据存在，但 empirical support 不够强，criterion grounding 也不完整。它说明为了避免 false accept，系统需要诚实保留不确定性，而不是把所有正向信号都映射成 accept。

## Borderline positive gold reject: `WNxlJJIEVj`

- gold decision: `reject`
- final recommendation view: `borderline_positive`
- support summary: `real=2, nonabs=2, ind=2, emp=2`
- positive grounded criteria: `significance_contribution, empirical_adequacy`
- hard negative: `False`

**解释**：该样本是 gold reject，但也有 real/non-abstract/empirical support 和 positive criteria。它说明 positive support 不是 accept 的充分条件；如果没有可靠 negative blocker，系统不能安全地区分这类 false accept 风险。

## Not assessable gold accept: `QAAsnSRwgu`

- gold decision: `accept`
- final recommendation view: `not_assessable`
- support summary: `real=0, nonabs=0, ind=0, emp=0`
- positive grounded criteria: `none`
- hard negative: `False`

**解释**：该样本是 gold accept，但 final-view 中没有形成真实 strong support 或 positive grounded criteria。它代表当前证据形成失败类型：系统不是应该 reject，而是应该承认证据不足，输出 not_assessable。

## Reject-like gold reject: `a6SntIisgg`

- gold decision: `reject`
- final recommendation view: `reject_like`
- support summary: `real=2, nonabs=2, ind=2, emp=0`
- positive grounded criteria: `novelty_originality, technical_soundness, empirical_adequacy`
- hard negative: `True`

**解释**：这是少数 reject_like 样本。系统同时看到正向支持和 hard negative，最终推荐层把 grounded hard negative 作为主导信号。它说明 reject_like 目前覆盖率低，但这种标签比默认 reject 更可解释。

## Case-level 结论

1. `accept_like` 是高精度但低召回的正向推荐。
2. `borderline_positive` 混合 gold accept 与 gold reject，不能直接映射为 accept。
3. `not_assessable` 是系统诚实表达证据不足的必要类别，不应默认等同 reject。
4. `reject_like` 当前覆盖率低，说明 reliable negative blocker formation 仍是限制项。
