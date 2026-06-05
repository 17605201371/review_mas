# Fallback Flaw Lifecycle Guard v1

## 目标

防止 Critique / General Reviewer 的 JSON 解析失败被包装成真实 paper flaw。此前 `flaw-fallback-*` 可能以 `severity=major,status=candidate` 进入 state，并在 support-quality / recommendation audit 中表现为 hard-negative burden。

## 修改

- fallback critique flaw 统一标记为 `source=fallback-extraction`。
- fallback critique flaw 统一标记为 `grounding_status=fallback_unverified`。
- fallback critique flaw 降级为 `severity=minor,status=downgraded`。
- fallback critique 不再写 `recommendation=reject`，而是保持 `undecided`。
- `_normalize_flaw_item()` 中增加兜底保护：即使上游忘记标 source，只要 `flaw_id` 是 `flaw-fallback-*` 或文本明显是 malformed JSON / system meta，也自动降级。

## 边界

这不是新的 recovery/controller 机制，只是防止系统解析失败污染 paper weakness。真实 grounded flaw 仍保留原 severity/status。
