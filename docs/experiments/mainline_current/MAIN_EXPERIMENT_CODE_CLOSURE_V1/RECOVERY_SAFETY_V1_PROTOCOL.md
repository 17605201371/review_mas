# RECOVERY_SAFETY_V1_PROTOCOL

## 本轮代码级安全收口

新增 validator 约束：claim 被 recovery patch 降级到 `unsupported` 时，不能只引用 `supports / partially_supports` evidence。必须引用 contradiction、missing-evidence 或其他负向 grounding evidence。

## 为什么这样改

之前 recovery validator 只检查 evidence 是否存在并绑定目标 claim，但没有检查 evidence stance 是否支持该 lifecycle transition。这会允许“用支持证据证明 unsupported”的不安全 patch。现在这类 patch 返回：`EVIDENCE_SEMANTIC_MISMATCH`。

## 非目标

- 不提高 recovery commit 数。
- 不放宽 validator。
- 不新增 recovery controller。
- 不把 blocked patch 写成 final weakness。

## 测试

`tests/test_recovery_patch.py` 已覆盖：

- 支持证据不能把 claim 降成 unsupported。
- 矛盾证据可以支持 claim 降级 patch。
- status guard 仍可阻止后续 stale worker 重新抬高 claim。
- existing recovery parse / block / no-effect / target mismatch tests 继续通过。
