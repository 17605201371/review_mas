# Mainline-Final-v1 Next Step Decision

## 结论

当前已经可以进入 `Mainline-Final-v1` 收口阶段，但还不应直接把下一次大跑当成正式论文主实验。下一步应做 **9B 小确认**，而不是继续新增 controller 或继续调 final decision。

## 本轮 dry-run 关键发现

### 1. runtime 输入卫生已有明确改善，但 final decision 仍 collapse

`retained integrated` 与 `isolation v1.1` 都是 39/39 reject。说明当前不能把 accept/reject accuracy 当成唯一主指标。决策层仍然存在 reject collapse，但这个 collapse 不应通过简单阈值修复。

### 2. Evidence binding 已经稳定，但 positive support formation 仍不足

两个 fulltest39 源都显示：

- `fallback_strong_support_total = 0`
- `fallback_extraction_strong_support_total = 0`
- `strong_support_binding_precision = 1.0`

这说明 strong support 绑错 fallback claim 的主问题已被压下去。但 gold accept 仍缺少足够真实、非 abstract、独立的 strong support：`accept_rows_with_2plus_real_strong_support` 仍为 0 或极低。

### 3. isolation v1.1 比 retained bundle 更适合作为 runtime evidence 基线

`isolation v1.1` 相比 retained bundle：

- evidence fallback payload rate 更低：`0.0602` vs `0.1360`
- patch committed count 更高：`8` vs `0`
- rows with any commit 更高：`6` vs `0`

因此后续 Mainline-Final-v1 runtime 应优先以 Evidence fallback target isolation v1.1 为基线，而不是根目录 retained bundle 中仍带有旧 support formation / fallback target 痕迹的路径。

### 4. final-view flaw lifecycle 必须进入 report hygiene 层

`Final-View Flaw Lifecycle v1` 显示：

- `borderline = 15`
- `not_assessable = 18`
- `reject_like = 6`

同时存在大量 excerpt / fallback / malformed / ungrounded candidate flaw。这说明 final report 不能继续把系统限制和未验证疑点写成 hard paper weakness。该层应进入 final-view/report hygiene，但不接入 live state。

### 5. criterion layer 可以保留，但还不是 decision rule

criterion audit 显示：

- significance / soundness coverage 较高；
- novelty / clarity coverage 偏低；
- empirical grounding 仍弱。

criterion-aware report 对论文叙事有价值，但 novelty/soundness/empirical 维度暂时不应直接决定 accept/reject。

## Mainline-Final-v1 固定边界

### Runtime 保留

- `p25.1 + explicit recovery phase`
- Evidence Binding Robustness
- Evidence JSON Robustness v1.1
- Evidence fallback target isolation v1.1
- config alignment / observability

### Offline / final-view 保留

- final-view hygiene
- support quality / evidence independence audit
- criterion coverage & grounding audit
- criterion-grounded report section
- flaw lifecycle / meta-leakage classification

### 不进入主线

- Support Formation Pass runtime
- Evidence Context Selection v2 runtime
- sticky / throttle / progression gate
- recovery entry defer
- live state hygiene mutation
- final decision 阈值硬调
- medium support 直接升级为 strong

## 下一步唯一建议

下一步做：

```text
Mainline-Final-v1 9B Confirmation Small Set
```

规模建议：5–8 条，不开 full 9B。样本应包含：

- 2–3 条 gold accept，尤其是当前 not_assessable / borderline 的 accept；
- 2 条 reject-like reject；
- 1–2 条 meta-leakage / fallback artifact 明显的 case；
- 1 条 criterion empirical grounding 弱的 case。

目标不是直接看 9B accuracy，而是确认：

1. Evidence binding precision 是否保持；
2. fallback payload 是否不回升；
3. non-abstract / empirical support 是否增加；
4. final-view flaw lifecycle 是否仍能把 meta/artifact 从 Key Weakness 分离；
5. criterion report 是否更 grounded。

## 为什么不继续修 4B

4B 已经足够暴露结构问题：binding、fallback、flaw lifecycle、criterion grounding。继续在 4B 上新增 controller 容易回到局部修补。现在更有价值的是用 9B 小确认判断：这些结构化约束在更强模型上是否形成更高质量的 positive support 与更少 meta-leakage。

## Go / No-Go

### Go：进入 9B fulltest39 主试验

如果 9B 小确认满足：

- binding precision 保持高；
- fallback payload 不显著上升；
- accept 样本 non-abstract / empirical support 有提升；
- report 中 meta/excerpt/fallback artifact 不再进入 Key Weakness；
- criterion grounding 不恶化。

### No-Go：回到 evidence/report 层小修

如果出现：

- 9B 仍主要生成 abstract-only support；
- fallback payload 回升；
- criterion report 看起来更丰富但 grounding 下降；
- meta-leakage 仍进入 Key Weakness。

则不要开 full 9B，先做 Evidence output robustness 或 final report rendering 小修。
