# WEBGPT_9B_FULLTEST39_RERUN_20260429

用途：给网页 GPT 分析的 9B fulltest39 rerun 结果包。

## 文件

- `WEBGPT_9B_FULLTEST39_RERUN_20260429.jsonl`: 39 条 9B S4 推理结果。
- `WEBGPT_9B_FULLTEST39_RERUN_20260429.log`: 主运行日志。
- `WEBGPT_9B_FULLTEST39_RERUN_20260429_turn_logs.tar.gz`: turn-level logs 压缩包。
- `WEBGPT_9B_FULLTEST39_RERUN_20260429.config.json`: 本轮运行配置。

## 运行口径

- model: `/reviewF/datasets/Qwen3___5-9B`
- dataset: `/reviewF/datasets/drmas_review/test.parquet`
- split: `test`
- mode: `s4`
- limit: `39`
- max_turns: `8`
- max_model_len: `3072`
- max_tokens: `640`
- temperature/top_p: `0.2 / 0.95`
- max_num_seqs: `64`

## 快速摘要

- rows: `39`
- runtime final_decision: `reject=39`
- avg_reward: `0.4284`
- median_reward: `0.4794`

说明：这是 runtime 原始结果包；final-view hygiene / criterion-aware report / final recommendation view 等离线分析需要基于该 jsonl 另行生成。
