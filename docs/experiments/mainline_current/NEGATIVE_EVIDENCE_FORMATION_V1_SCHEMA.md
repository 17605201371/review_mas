# Negative Evidence Formation / Flaw Confirmation v1 Schema

## 定位

本轮是离线 formation audit，不改 runtime、不改 final decision、不使用 reviewer comments 作为模型输入。

## 核心对象

- `system_trusted_negative_blocker`: 已绑定真实 claim、非 fallback evidence、核心 criterion 相关，并能解释 empirical/soundness/novelty/significance 负向判断的 blocker。
- `system_weak_negative_candidate`: 有 paper/criterion 语言，但缺少真实负向 evidence 或确认生命周期，只能作为 report warning / human review signal。
- `negative_formation_gap`: oracle-style reviewer comments 指出 core hard weakness，但系统没有 trusted negative blocker。

## 进入 trusted blocker 的最小条件

1. 负向 evidence 必须绑定真实 claim，且不是 `fallback-extraction`。
2. flaw 必须是 `confirmed` 且 `major/critical`，并有真实负向 evidence 支撑。
3. unresolved 只有在绑定真实负向 evidence 且关联核心 criterion 时才可视为 paper-grounded blocker。
4. meta / excerpt / fallback / system limitation 不得作为 reject blocker。

## 本轮约束

该 schema 只用于决定下一轮是否值得做 Negative Evidence Formation / Flaw Confirmation pass，不直接进入最终推荐。
