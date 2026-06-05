# Fallback Flaw Lifecycle Guard v1 Sanity

## 静态验证

- `agent_system/environments/env_package/review/state.py` 语法检查通过。
- `agent_system/inference/review_runner.py` 语法检查通过。
- 新增单元测试覆盖 fallback flaw normalization。

## 测试

`PYTHONPATH=/root/zssmas_mainline pytest -q tests/test_review_decision_hygiene.py`

结果：`10 passed`。

## 当前限制

本轮尚未重跑 fulltest39。下一步需要用 4B 确认 runtime 中 fallback flaw 是否不再成为 trusted hard-negative。
