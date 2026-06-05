# PRE9B Evidence JSON Robustness Fix v1

## 背景

`mainline_final_v1_pre9bfix_9b_fulltest39_20260503` 的 9B fulltest39 结果不能作为正式主试验依据。旧 controller 已经关闭，但 Evidence Agent 的结构化输出在 9B 下大面积失败：

- `evidence_json_fallback_payload_turns=87`
- `fallback_used=87`
- `real_strong_support_total=1`
- `nonabstract_strong_support_total=1`
- `predicted_accept_count=0`

这说明当时主瓶颈不是 final decision policy，而是 Evidence JSON 输出/解析没有稳定进入 `ReviewState`。

## 根因

本轮审计确认了两个硬问题。

1. `scripts/run_review_infer.py` 直接运行时没有把 repo root 放到 `sys.path` 最前面，存在导入环境中旧版 `agent_system` 的风险。此前脚本直跑时看不到当前代码中的 `--seed` 和新增参数，说明服务器测试可能没有完全使用当前仓库代码。
2. Qwen3.5-9B 在 plain prompt 下经常回显 Evidence prompt 的 `Output contract` 或 schema 片段，导致 `<json>` 块为空、多个 JSON 对象混杂、或 prompt contract 文本被 fallback 当作 evidence 写入。

## 本轮修复

- `scripts/run_review_infer.py`：启动时强制将 repo root 插入 `sys.path[0]`，保证服务器运行使用当前仓库代码。
- `extract_tagged_json(...)`：改为候选式 JSON 提取，支持多个 `<json>...</json>` 块、fenced JSON、平衡大括号 JSON 对象，并按 schema key 选择最像 agent payload 的对象，避免被空 `<json>` 或嵌套 evidence item 误导。
- Evidence fallback：如果 malformed output 是 prompt/schema echo，不再生成 fallback evidence，只记录 unresolved，避免 `Output contract` 这类系统文本污染 evidence map。
- `VllmReviewGenerator`：新增 `--use-chat-template`，默认关闭；9B confirmation 可显式开启 tokenizer chat template，避免 9B plain prompt echo。

## 验证

- `tests/test_review_inference_runner.py` 与 `tests/test_review_decision_hygiene.py`：92 passed。

### 离线重放

基于旧 9B fulltest39 的 `runner_trace.raw` 重放新 parser：

- 旧解析：`json_valid=27`、`fallback_used=87`、`invalid_json=25`、`partial_recovered=2`
- 新 parser 离线重放：`json_valid=52`、`fallback_used=89`

结论：parser 能修复一部分 malformed/多 JSON 输出，但对 55 个短 `Output contract` echo 没有内容可恢复，必须启用 chat template。

### 9B smoke2

`mainline_final_v1_9b_jsonfix_smoke2_20260503`，2 条样本，启用 `--use-chat-template`：

- Evidence JSON 状态：`json_valid=12/12`
- `fallback_used=0`
- prompt-contract echo：0

### 9B balanced5

`mainline_final_v1_9b_jsonfix_balanced5_20260503`，5 条 balanced subset，启用 `--use-chat-template`：

- Evidence JSON 状态：`json_valid=30/30`
- `evidence_json_fallback_payload_turns=0`
- `fallback_strong_support_total=0`
- `real_strong_support_total=1`
- `empirical_strong_support_total=1`
- `predicted_accept_count=0`

## 结论

本轮修复应保留。它解决了 9B confirmation 的基础工程问题：当前代码被正确加载，Evidence JSON 不再大面积 fallback。

但 balanced5 也说明，JSON 修好后，下一层瓶颈变成 evidence context / support quality：9B 能稳定输出 JSON，但多数 Evidence Agent 判断仍是 `medium/missing`，因为可见 paper excerpt 中缺少足够具体的 result/table/experiment 证据。

下一步不要调 final decision，也不要恢复 controller。应先扩大到一个 9B 小确认集或 fulltest39 时启用 `--use-chat-template`，并重点审计 support quality / evidence context coverage。
