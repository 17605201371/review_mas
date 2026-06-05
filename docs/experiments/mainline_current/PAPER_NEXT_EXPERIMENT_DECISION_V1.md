# Paper Next Experiment Decision v1

## 当前判断

当前已经进入论文主线收口阶段，不应再继续新增 controller。下一步应围绕 `Mainline-Final-v1` 做论文表格、case study 和小范围确认。

## 下一步唯一建议

做 `Paper Result Pack v1` 的人工/脚本化整理：

1. 主表：runtime health、support state、criterion grounding、recommendation view。
2. Casebook：每类 recommendation 选择代表样本。
3. Negative findings：sticky/throttle/negative blocker/live hygiene 的限制。
4. 写作草稿：把系统定位为 evidence-grounded review assistance，而不是黑箱 accept/reject classifier。

## 暂时不做

- 不跑新的 9B full experiment。
- 不调 final decision 阈值。
- 不把 criterion 分数直接接入 decision。
- 不继续 sticky / throttle / progression gate。
- 不继续 negative blocker formation pass。
