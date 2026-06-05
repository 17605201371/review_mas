# Criterion-Aware Final Report Section v1 Sanity

## 检查项

- `render_final_review(...)` 已加入 `4. Criterion Assessment`。
- 该章节包含五个维度：novelty、significance、soundness、empirical adequacy、clarity/reproducibility。
- `infer_final_decision(...)` 未修改。
- 有证据时，criterion 文案会引用 claim/evidence id。
- 缺少 grounding 的维度使用 `not_assessable` 或保守表述。

## 验证结果

- `python -m py_compile agent_system/environments/env_package/review/state.py` 通过。
- `pytest -q tests/test_review_multiturn.py::test_render_final_review_includes_grounded_criterion_section_without_changing_decision` 通过。
- `pytest -q tests/test_review_multiturn.py` 通过，结果为 `7 passed`。

## 已知测试状态

更大范围运行 `pytest -q tests/test_review_multiturn.py tests/test_review_inference_runner.py` 时，`tests/test_review_inference_runner.py` 仍有 manager/progression-throttle 相关旧失败。这些失败来自 manager policy 期望不一致，和本轮 report-only 改动无关。
