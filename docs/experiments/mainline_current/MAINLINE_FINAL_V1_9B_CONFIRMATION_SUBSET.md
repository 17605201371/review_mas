# Mainline-Final-v1 9B Confirmation Subset

## 目标

本 subset 用于主试验前 9B 小确认，不作为正式 fulltest。目标是检查 `Mainline-Final-v1` 在更强模型下是否保持 evidence binding / fallback isolation / final-view flaw lifecycle / criterion grounding 的方向一致性。

## 样本列表

| paper_id | gold | 4B derived flaw label | 入选理由 |
|---|---|---|---|
| `hj323oR3rw` | accept | borderline | accept 样本，medium support only，fallback/malformed flaw artifact |
| `LebzzClHYw` | accept | borderline | accept 样本，abstract-only strong support，测试 9B 是否能形成 non-abstract support |
| `QAAsnSRwgu` | accept | not_assessable | accept 样本，excerpt limitation 进入 hard weakness 的典型 case |
| `jVEoydFOl9` | accept | not_assessable | accept 样本，system/meta limitation 与 fallback target 污染明显 |
| `X41c4uB4k0` | accept | not_assessable | historical sentinel，fallback/malformed flaw artifact |
| `ZHr0JajZfH` | reject | reject_like | grounded confirmed flaw reject，用于确认 reject blocker 不被误放松 |
| `kam84eEmub` | reject | reject_like | grounded confirmed flaw + excerpt limitation，测试 report hygiene |
| `TPAj63ax4Y` | reject | reject_like | grounded candidate reject，用于检查 candidate vs confirmed 分层 |

## 固定配置

- model: `/reviewF/datasets/Qwen3___5-9B`
- mode: `s4`
- max_turns: `8`
- max_workers_per_turn: `2`
- manager_batch_size: `2`
- max_model_len: `3072`
- max_tokens: `640`
- temperature: `0.2`
- top_p: `0.95`
- seed: `20260429`

## 观察指标

本轮不以 accuracy 为主，主要看：

1. binding precision 是否保持；
2. fallback payload 是否不回升；
3. accept 样本 non-abstract / empirical support 是否改善；
4. final-view flaw lifecycle 是否仍能把 meta/artifact 从 Key Weakness 分离；
5. criterion grounding 是否不恶化。
