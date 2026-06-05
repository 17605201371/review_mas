# Fallback Flaw Lifecycle Guard v1 Decision

## 结论

保留该修复。它修的是明确实现错误：系统 fallback / malformed critique 不应被当成论文的 major flaw。

## 为什么现在先修它

Soft Focus v2 的 audit 显示，`LebzzClHYw` 已满足 high-precision accept-like 条件，但仍在 raw flaw 统计中带有 `flaw-fallback-*` major candidate。`NnExMNiTHw` 的 false accept 也暴露出必须区分真实 hard-negative 与 fallback/meta flaw。

## 下一步

先跑 4B 确认：

- trusted hard-negative 是否下降；
- fallback/meta flaw 是否仍可记录但不阻断；
- high-precision accept-like 是否仍保持 false accept 为 0；
- runtime 不应因为 fallback flaw 降级而大幅放松。

通过后，再考虑 `Method / Soundness Evidence Formation v1`。
