# Model Transfer Diagnosis 20260605

## 结论

网页 GPT 提到的“模型能力被框架压平”有参考价值，但不能直接沿用“DeepSeek V3.2 没有比 9B 强多少”这个结论。按完整 8 样本重新对齐后，DeepSeek API 版在 evidence 侧明显强于 Qwen 9B：

| 指标 | Qwen 9B same8 | DeepSeek full8 | 判断 |
|---|---:|---:|---|
| avg reward | 0.4573 | 0.5060 | DeepSeek 更高 |
| avg evidence_support_score | 0.2687 | 0.3854 | DeepSeek 更高 |
| raw payload evidence total | 19 | 57 | DeepSeek 明显更多 |
| final support total | 13 | 24 | DeepSeek 更高 |
| final support from fallback | 11 | 0 | DeepSeek 更少依赖兜底 |
| fallback final-support rate | 0.8462 | 0.0000 | DeepSeek 更像模型主动产证 |
| independent final support groups | 13 | 19 | DeepSeek 更高 |

所以当前更准确的判断是：

> DeepSeek 的模型能力已经体现在 raw evidence payload、direct final support 和 fallback dependency 下降上；但 final decision、grounded weakness、recovery effective repair 没有同步变强，因此论文叙事不能只看最终 reward 或 accept/reject。

## 为什么旧结论会显得悲观

旧的 `deepseek_v3_vs_qwen35_comparison_report.md` 只统计了 4 篇 `smoke8_20260605_deepseek_v3_sameids_t7.jsonl`，而不是完整的 `local_deepseek_v3_full8.jsonl`。前 4 篇里 DeepSeek evidence support 平均低于 Qwen，但完整 8 篇中 DeepSeek 反超。

这说明模型对比必须用完整同 ID 样本和统一 dashboard 口径，否则容易把局部波动误判为“强模型无效”。

## 当前真正的系统瓶颈

### 1. Final-view 过滤仍然是最大压缩点

DeepSeek full8 的 support trace：

```text
support_trace_total = 68
support_trace_included = 23/24 左右
support_trace_dropped = 33
主要 drop reason:
  hygiene_filtered = 17
  semantic_mismatch = 9
  weak_support_depth = 7
```

这说明 DeepSeek 生成了更多 evidence，但相当一部分被 final-view guard 压掉。下一步如果要继续提升，应优先分析 `hygiene_filtered` 是否过严，而不是继续换模型。

### 2. Flaw / negative evidence 没有随大模型增强

DeepSeek full8 的 positive support 更强，但 grounded weakness 仍然为 0，negative evidence 主要是 scope limitation：

```text
verified_negative_flaw_count = 4
verified_actionable_negative_flaw_count = 0
grounded_weakness_count = 0
negative_type_scope_limitation = 4
```

这说明大模型能够更好地产生正向 evidence，但当前 negative evidence schema / Critique Agent / final-view flaw lifecycle 仍然没有把“真缺陷”打通。

### 3. Recovery 仍不是主要收益来源

Qwen8 和 DeepSeek full8 的 `recovery_effective_repair` 都是 1。DeepSeek 没有显著改善 recovery，这说明 recovery 现在主要受 target gate、validator、patch operation 限制，而不是底层语言模型能力。

论文里应把 recovery 继续定位为状态修复与安全验证机制，而不是当前性能提升的主要来源。

### 4. Final decision 仍不适合作为主指标

两个模型 final_decision 仍基本是 `reject`。DeepSeek 在 evidence 质量上提升，但 binary decision 没有对应变化。这再次说明：accept/reject 应只作为 health check，论文主指标应围绕 evidence grounding、support survival、flaw lifecycle、recovery delta 和 final report hygiene。

## 对网页 GPT 判断的修正

我认同以下部分：

- 框架确实可能通过 quote bank、schema、verifier、final-view guard 压缩模型差异。
- 需要报告 raw payload → accepted support → final support 的漏斗，而不是只看 final reward。
- 需要区分框架不变量和模型适配层。
- 当前 negative/flaw/recovery 仍然是机制瓶颈。

我不认同或需要修正的部分：

- 不能说 DeepSeek 没有比 9B 强。完整 8 样本显示 DeepSeek 的 direct evidence formation 明显更强。
- 不能只用前 4 篇的旧报告支撑结论。完整 full8 和 batch2 才是更可靠的判断。
- 不能把问题归因于 prompt 过拟合 Qwen 后就停止。当前证据显示 DeepSeek 在同 prompt 下已经能减少 fallback，这正好支持框架的跨模型可迁移性。

## 下一步建议

1. 固定 `scripts/analyze_model_transfer_funnel_v1.py` 作为跨模型分析脚本。
2. 更新论文实验表：同时报告 Qwen 9B、DeepSeek full8、DeepSeek batch2 的 funnel，而不是只报告 reward。
3. 继续优化 final-view support drop，重点审计 `hygiene_filtered` 和 `semantic_mismatch`。
4. 单独做 negative/flaw/recovery 改进，不要指望换模型自然修好。
5. 如果继续做模型适配，不应放松 ReviewState/verifier，而应增加可控的 context request / quote bank expansion / model-profile prompt 层。

