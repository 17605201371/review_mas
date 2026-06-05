# Final Recommendation Policy v1 Dry Run Decision

## 结论

可以进入 `9B Fulltest39 Dry Run`，但不是正式主试验，也不是 runtime decision 上线。

理由：

- 9B confirmation + safety gate 在 8 条确认集上恢复 4 个 accept，false accept 为 0。
- 4B fulltest39 仍无法恢复 accept，说明问题不是 policy 本身无效，而是 4B support/criterion grounding 不足。
- 当前 policy 已经比 strong-support-count 更符合论文目标：它把 recommendation 拆成 `accept_like / reject_like / borderline / not_assessable`，并用 negative evidence gate 控制 false accept。

## 进入 9B dry run 的条件

下一轮 9B fulltest39 dry run 必须满足：

1. 不改 runtime；
2. 不新增 sticky/throttle/gate/controller；
3. 使用当前保留主线组件；
4. 离线应用 `Final Recommendation Policy v1`；
5. 同时输出 decision health、support quality、criterion grounding、flaw lifecycle、meta leakage。

## 暂时不要做

- 不要把 policy 接入 live final decision。
- 不要把 criterion 低分直接作为 reject 规则。
- 不要重新打开 sticky/throttle/progression gate。
- 不要把 9B dry run 当正式论文主实验。
