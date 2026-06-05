# EVIDENCE_JSON_CONTRACT_V1_PROTOCOL

## 目标

本轮只修 Evidence Agent 的结构化输出契约，不改 final decision、recovery、state hygiene、criterion/report 逻辑。

最新审计显示，当前主线已经基本解决 Evidence context 可见性问题：Evidence prompt 中能看到 empirical/table/method 片段；剩余断点主要是 Evidence Agent 经常把输出预算消耗在推理文本中，导致 `<json>` 未开始、未闭合或 JSON 截断，最终触发 fallback payload。

## 改动

1. `agent_system/review_prompts.py`
   - Evidence Prompt 从 `think + json` 改成 `JSON-only`。
   - 明确禁止 reasoning text、markdown、prose、bullet list。
   - 保留 allowed claim id 绑定、强支持只用于 method/result/table/figure/ablation 证据、最多 2 条 evidence。

2. `agent_system/inference/review_runner.py`
   - 新增 Evidence JSON contract status 记录。
   - 对 Evidence Agent 输出分类：`json_valid`、`partial_recovered`、`fallback_used`、`raw_empty`、`no_json_object`、`truncated_tagged_json`、`truncated_json_object`、`invalid_json`。
   - 同时写入 runner trace 和 manager payload，便于 turn log 汇总。

3. `agent_system/environments/env_package/review/state.py`
   - turn log 新增 Evidence JSON contract 字段：
     - `evidence_json_contract_mode`
     - `evidence_json_parse_status`
     - `evidence_json_failure_type`
     - `evidence_json_parse_error`
     - `evidence_json_partial_recovery`
     - `evidence_json_fallback_payload_used`
     - `evidence_json_raw_chars`
     - `evidence_json_prompt_chars`

## 非目标

- 不调 accept/reject 阈值。
- 不把 criterion 维度接入 decision。
- 不改变 recovery / sticky / throttle / gate。
- 不改变 live state hygiene。
- 不扩大 context 或 max_model_len。

## 评估口径

下一次可用 GPU 时，优先跑 4B 小样本，再跑 39 样本。核心指标：

- Evidence Agent parse error count
- Evidence fallback payload count
- evidence_json_parse_status 分布
- real strong support
- empirical strong support
- fallback strong support
- final decision 只作健康检查
