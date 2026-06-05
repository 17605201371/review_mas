# Method / Soundness Next-Cut Decision

## 当前判断

修正 trusted hard-negative 口径后，Soft Focus v2 的剩余瓶颈分成两层：

1. `flaw-fallback-*` / malformed critique 不能算真实 paper flaw，这类问题必须在 runtime fallback flaw lifecycle 中降级。
2. 对仍未进入 `accept_like` 的样本，主要缺口是 method support、soundness/novelty positive、empirical support depth 和 open unresolved burden。

因此，下一刀不应继续放宽 final recommendation，也不应恢复 sticky / throttle / progression gate。

## 关键证据

- gold accept 数：9
- accept_like 数：1
- borderline_positive 数：9
- gold accept 中具备 method support 的样本数：4
- gold accept 中 soundness positive 的样本数：4
- runtime false accept：NnExMNiTHw
- gold accept blocker family：{'hard_negative_burden': 5, 'support_depth_gap': 2, 'passes_or_other': 1, 'method_soundness_gap': 1}
- borderline blocker family：{'hard_negative_burden': 6, 'method_soundness_gap': 3}

## 本轮已执行的最小修复

实现 `Fallback Flaw Lifecycle Guard v1`：Critique / General Reviewer fallback 解析失败不再生成 `major candidate flaw`，而是写成 `severity=minor`、`status=downgraded`、`source=fallback-extraction`、`grounding_status=fallback_unverified`，并且 recommendation 保持 `undecided`。这属于 bug fix，不是新 controller。

## 下一轮唯一建议

先用 4B 小确认或 fulltest39 重跑验证 `Fallback Flaw Lifecycle Guard v1`：

1. `trusted_major_or_critical_flaws` 是否下降。
2. `fallback_or_meta_flaws` 是否仍可观测但不再阻断 accept-like。
3. `LebzzClHYw` 这类 accept_like 是否不再被 fallback flaw 污染。
4. false accept `NnExMNiTHw` 是否仍被 method/soundness/novelty blocker 挡住。

如果确认稳定，再进入 `Method / Soundness Evidence Formation v1`，优先补 method/mechanism/assumption 与 result/table 的配对证据。

## 暂时不做

- 不放宽 `high_precision_criterion_quality`。
- 不把 `borderline_positive` 映射 accept。
- 不恢复 sticky / throttle / progression gate。
- 不做大规模 9B 正式主试验，先做 4B 确认。
