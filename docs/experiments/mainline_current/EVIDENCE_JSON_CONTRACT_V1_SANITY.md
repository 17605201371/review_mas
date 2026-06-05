# EVIDENCE_JSON_CONTRACT_V1_SANITY

## 静态验证

- `python3 -m py_compile agent_system/review_prompts.py agent_system/inference/review_runner.py agent_system/environments/env_package/review/state.py` 通过。
- focused tests 通过：`9 passed in 1.44s`。
  - `tests/test_review_inference_runner.py::test_evidence_observation_omits_fallback_claim_targets`
  - `tests/test_review_decision_hygiene.py`

## 冒烟运行状态

尝试启动 4B 2-row smoke，但当前 GPU 显存不足：

- free memory: 2.56 / 23.52 GiB
- requested by vLLM at gpu_memory_utilization=0.9: 21.16 GiB

因此本轮未强行杀进程，也未得到有效 model-run 结果。失败的 smoke 输出文件已删除，避免污染结果目录。

## 当前结论

代码级修复已落地，但需要等 GPU 空闲后再跑 4B 小样本确认。预期第一观察点不是 accuracy，而是 Evidence Agent 的 parse/fallback 是否下降，以及 `evidence_json_parse_status` 是否能在 turn log 中稳定落盘。
