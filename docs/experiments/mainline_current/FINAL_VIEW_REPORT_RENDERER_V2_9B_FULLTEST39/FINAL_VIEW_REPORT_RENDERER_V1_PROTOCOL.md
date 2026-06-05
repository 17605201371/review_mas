# Final-View Report Renderer v1 Protocol

## 定位

本轮是离线 final report 渲染，不改 runtime、不改 live `ReviewState`、不重跑模型、不改变已有 accept/reject。

## 输入

- fulltest39 运行后的 final `ReviewState` / final report。
- `Final-View Unresolved / Candidate-Flaw Classifier v1` 的分类结果。

## 渲染原则

- confirmed / trusted grounded hard flaw 才进入 `Confirmed Weaknesses`。
- candidate hard flaw 进入 `Potential Concerns`，不能等同 confirmed weakness。
- fallback / malformed JSON / system-meta / excerpt limitation 进入 `Review Limitations`。
- paper-grounded open items 进入 `Unresolved Questions`。
- criterion section 只报告 coverage / grounding / unsupported / meta-leakage 状态，不参与 runtime final decision。

## 边界

本轮目标是让 final report 更符合论文主线：证据对齐、状态卫生、维度可诊断。它不是新的决策阈值，也不是 controller 改动。
