# Negative Evidence Formation v1 Decision

## 决策

下一步应做 **Negative Evidence Formation / Flaw Confirmation v1 小样本 pass**，而不是继续调 final decision 阈值或重启 sticky/throttle。

## 依据

- false accept: `7` 行。
- false accept 中 trusted blocker 行数: `0`。
- false accept 中 formation gap 行数: `7`。
- recovered accept 中同样存在 oracle hard weakness: `3`，所以 reviewer comments 不能直接作为 reject rule。

## 下一刀

实现一个小样本 negative evidence / flaw confirmation pass：

1. 只围绕 empirical / soundness / novelty / significance 四个核心 criterion。
2. 输入只能用 paper text、当前 ReviewState、claim/evidence/flaw，不使用 reviewer comments。
3. 输出结构化 `negative_evidence_items` 和 `flaw_confirmation_items`。
4. 只有真实 claim 绑定、非 fallback、paper-grounded、criterion-linked 的负向证据才能成为 trusted blocker。
5. 先在 false accept + recovered accept 的 10 条 diagnostic subset 上跑，不进入正式主试验。

## 暂时不做

- 不把 weak negative candidate 当 reject blocker。
- 不用 unresolved/meta count 直接 reject。
- 不改 final decision 阈值。
- 不做 9B full rerun。

## 成功标准

- false accept 中至少形成部分 trusted negative blocker。
- recovered accept 不被同样规则大面积误伤。
- trusted blocker 能指向具体 criterion、claim/evidence 或 paper excerpt。
