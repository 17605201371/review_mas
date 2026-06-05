# Evidence ID Turn-Scoping v1 Sanity

## 静态检查

- `review_runner.py` 和 `state.py` 已通过 `py_compile`。
- 相关 review runner 单测和 decision hygiene 单测通过。

## Smoke 结果

2 条 smoke 样本中，Evidence Agent payload 和 final ReviewState 都出现 turn-scoped evidence id，例如：

```text
evidence-1-turn-2
evidence-2-turn-2
```

## 观测字段

`evidence_id_scope_map` 已成功落入 turn log，例如：

```json
{"evidence-1": "evidence-1-turn-2", "evidence-2": "evidence-2-turn-2"}
```

## 明显错误

- 未发现 payload evidence_id 重复。
- 未发现 final ReviewState evidence_id 重复。
- 未发现 stuck / loop。

结论：sanity 通过，可以进入 mixed16 功能验证。
