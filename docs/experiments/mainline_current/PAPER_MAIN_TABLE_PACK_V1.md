# Paper Main Table Pack v1

## 定位

这是论文写作用的主表草案，不是新的实验。它把 clean 4B 和最新 9B context v2.2 的核心结果压成同一套口径，方便写 Method / Results / Discussion。

## Table A: Evidence / Support Construction

| version | rows | real strong | non-abstract strong | empirical strong | fallback strong | binding precision | json invalid/missing | legacy controller turns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clean 4B fulltest39 | 39 | 28 | 25 | 20 | 0 | 1.0 | 27 | 0 |
| 9B context v2.2 fulltest39 | 39 | 49 | 49 | 38 | 0 | 1.0 | 0 | 0 |

## Table B: Decision Health Check

| version | accuracy | macro-F1 | accept recall | reject recall | pred accept | false accept | false reject |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clean 4B fulltest39 | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 | 9 |
| 9B context v2.2 fulltest39 | 0.7692 | 0.4348 | 0.0 | 1.0 | 0 | 0 | 9 |

## Table C: State / Recovery Burden

| version | unresolved | evidence gaps | flaws | conflicts | patch emitted | patch committed | rows with commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Clean 4B fulltest39 | 190 | 147 | 51 | 79 | 109 | 6 | 6 |
| 9B context v2.2 fulltest39 | 269 | 110 | 48 | 73 | 96 | 1 | 1 |

## Table D: 9B Recommendation View v2

| view | count |
| --- | --- |
| borderline_insufficient | 2 |
| borderline_positive | 15 |
| not_assessable | 21 |
| reject_like | 1 |

## Table E: 9B Final-View Report Partition

| metric | value |
| --- | --- |
| confirmed weaknesses | 2 |
| potential concerns | 4 |
| review limitations | 103 |
| unresolved questions | 228 |
| reports with confirmed weakness | 2 |
| confirmed weakness meta-leak rows | 0 |

## Table F: 9B Criterion Grounding Counts

| criterion | covered | grounded | meta leakage |
| --- | --- | --- | --- |
| novelty | 10 | 10 | 3 |
| significance | 36 | 9 | 2 |
| soundness | 29 | 7 | 19 |
| empirical | 28 | 4 | 3 |
| clarity | 10 | 14 | 8 |

## 论文解释建议

1. 不把 runtime accept/reject 作为主贡献：9B 仍然 39/39 reject，说明 binary recommendation policy 不是当前系统最可信输出。
2. 把主贡献写成 state/report construction：Evidence Binding、JSON robustness、positive support formation、criterion grounding、final-view report hygiene。
3. 把 final-view recommendation 作为审稿辅助输出：`borderline_positive` 与 `not_assessable` 比强行 accept/reject 更符合系统定位。
4. Recovery 保留为结构化修复模块，但当前有效 commit 低，不应包装成主要增益。
