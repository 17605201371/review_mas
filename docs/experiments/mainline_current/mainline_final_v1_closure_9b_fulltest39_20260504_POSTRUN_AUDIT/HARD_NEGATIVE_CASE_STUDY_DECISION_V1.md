# HARD_NEGATIVE_CASE_STUDY_DECISION_V1

## 决策

暂不把 hard-negative extraction runtime 化，也不把 borderline_positive 直接映射为 accept。保留当前 final-view recommendation 的保守投影，并把 hard-negative grounding 作为论文 case-study / audit 指标。

## 原因

1. high-support reject 多数缺少稳定 paper-grounded hard-negative blocker，说明不能靠 support 数量做 accept。
2. accept-protect 样本仍需要避免被 stale gap / meta unresolved 压制，说明 raw negative burden 也不能直接做 reject。
3. 当前最符合论文目标的结论是：系统能形成正向证据，但 final recommendation 必须区分 grounded hard-negative 与系统不确定性。

## 下一步

选取 2 个 high-support reject 和 2 个 accept-protect 样本，写 paper-ready case studies；不新增 controller，不硬调 binary decision。
